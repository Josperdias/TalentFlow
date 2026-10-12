package br.com.talentflow.people.data

import android.app.Application
import android.content.Context
import android.os.Build
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import br.com.talentflow.core.ApiClient
import br.com.talentflow.core.ApiException
import br.com.talentflow.core.ApplicationRow
import br.com.talentflow.core.AuthExpiredException
import br.com.talentflow.core.ChangeFeed
import br.com.talentflow.core.Job
import br.com.talentflow.core.JobDetail
import br.com.talentflow.core.Leave
import br.com.talentflow.core.NetworkException
import br.com.talentflow.core.Plan
import br.com.talentflow.core.Portal
import br.com.talentflow.core.UpdateInfo
import br.com.talentflow.core.UpdateIntegrityException
import br.com.talentflow.core.Updater
import br.com.talentflow.core.ServerUrl
import br.com.talentflow.core.SessionInfo
import br.com.talentflow.core.User
import br.com.talentflow.core.candidates
import br.com.talentflow.core.createJob
import br.com.talentflow.core.dashboard
import br.com.talentflow.core.decideLeave
import br.com.talentflow.core.employees
import br.com.talentflow.core.insights
import br.com.talentflow.core.isVersionBelow
import br.com.talentflow.core.jobDetail
import br.com.talentflow.core.jobs
import br.com.talentflow.core.me
import br.com.talentflow.core.leaves
import br.com.talentflow.core.moveApplication
import br.com.talentflow.core.plans
import br.com.talentflow.core.portal
import br.com.talentflow.core.revokeOtherSessions
import br.com.talentflow.core.sessions
import br.com.talentflow.core.setPlanAction
import br.com.talentflow.core.updateJobTitle
import br.com.talentflow.people.BuildConfig
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import java.io.IOException

sealed interface Phase {
    data object Boot : Phase
    data object NeedServer : Phase
    data class NeedLogin(val message: String? = null) : Phase
    data class Unreachable(val message: String) : Phase
    data class Ready(val user: User) : Phase
}

enum class Connection { Connecting, Online, Offline }

/** Estados da atualização dentro do app (sem navegador): avisar -> baixar e conferir SHA-256 -> o Android confirma e instala. */
sealed interface UpdateState {
    data object Idle : UpdateState
    data class Available(val info: UpdateInfo) : UpdateState
    data class NeedsPermission(val info: UpdateInfo) : UpdateState
    data class Downloading(val info: UpdateInfo, val done: Long) : UpdateState
    data class WaitingConfirm(val info: UpdateInfo) : UpdateState
    data class Failed(val info: UpdateInfo?, val message: String) : UpdateState
}

/** Resultado de uma ação de escrita; conflito (409) tem tratamento próprio e nunca sobrescreve em silêncio. */
sealed interface ActionResult {
    data object Success : ActionResult
    data class Conflict(val message: String) : ActionResult
    data class Failure(val message: String) : ActionResult
}

class AppViewModel(app: Application) : AndroidViewModel(app) {
    private val prefs = app.getSharedPreferences("tf_prefs", Context.MODE_PRIVATE)
    private val tokenStore = KeystoreTokenStore(app)
    private var api: ApiClient? = null

    private val _phase = MutableStateFlow<Phase>(Phase.Boot)
    val phase: StateFlow<Phase> = _phase.asStateFlow()
    private val _connection = MutableStateFlow(Connection.Connecting)
    val connection: StateFlow<Connection> = _connection.asStateFlow()
    private val _notice = MutableStateFlow<String?>(null)
    val notice: StateFlow<String?> = _notice.asStateFlow()
    private val _update = MutableStateFlow<UpdateState>(UpdateState.Idle)
    val update: StateFlow<UpdateState> = _update.asStateFlow()
    private var lastUpdateCheck = 0L
    private val _server = MutableStateFlow(prefs.getString(KEY_BASE, null))
    val server: StateFlow<String?> = _server.asStateFlow()

    private fun client(): ApiClient = api ?: error("Sem servidor configurado")

    private fun <T> loadable(vararg entities: String, fetch: suspend () -> T) =
        Loadable(entities.toSet(), viewModelScope, ::onAuthExpired, fetch)

    val dashboard = loadable("job", "application", "interview", "offer", "task") { client().dashboard() }
    val insights = loadable("employee", "development_plan", "leave_request") { client().insights() }
    val jobs = loadable("job", "application") { client().jobs() }
    val candidates = loadable("candidate", "application") { client().candidates() }
    val employees = loadable("employee", "application") { client().employees() }
    val plans = loadable("development_plan") { client().plans("") }
    val leaves = loadable("leave_request") { client().leaves() }
    val portal = loadable<Portal>("application") { client().portal() }
    val sessions = loadable<List<SessionInfo>>() { client().sessions() }
    private val details = HashMap<Int, Loadable<JobDetail>>()
    private val all get() = listOf<Loadable<*>>(dashboard, insights, jobs, candidates, employees, plans, leaves, portal, sessions) + details.values

    fun jobDetail(id: Int): Loadable<JobDetail> =
        details.getOrPut(id) { loadable("job", "application", "job_stage", "interview", "scorecard") { client().jobDetail(id) } }

    init {
        boot()
        viewModelScope.launch {
            UpdateInstaller.failure.collect { msg ->
                if (msg != null) _update.value = UpdateState.Failed((_update.value as? UpdateState.WaitingConfirm)?.info, msg)
            }
        }
    }

    // ---------- sessão ----------
    fun boot() {
        _phase.value = Phase.Boot
        val base = prefs.getString(KEY_BASE, null)
        if (base == null) { _phase.value = Phase.NeedServer; return }
        api = newClient(base)
        viewModelScope.launch {
            if (!client().isSignedIn) { _phase.value = Phase.NeedLogin(); return@launch }
            try {
                val me = client().me()
                _phase.value = Phase.Ready(me); checkVersion(); checkUpdate(force = true)
            } catch (_: AuthExpiredException) {
                _phase.value = Phase.NeedLogin("Sua sessão expirou. Entre novamente.")
            } catch (e: ApiException) {
                _phase.value = if (e.status == 401) Phase.NeedLogin() else Phase.Unreachable(e.message ?: "Erro")
            } catch (e: NetworkException) {
                _phase.value = Phase.Unreachable(e.message ?: "Sem conexão")
            }
        }
    }

    /** Valida o endereço digitado e confere se a API responde antes de guardar. */
    fun setServer(input: String, onResult: (String?) -> Unit) {
        val base = ServerUrl.toApiBase(input, allowInsecure = BuildConfig.DEBUG)
        if (base == null) { onResult("Endereço inválido. Use https:// e o endereço do seu servidor."); return }
        viewModelScope.launch {
            try {
                val candidate = newClient(base)
                candidate.health()
                prefs.edit().putString(KEY_BASE, base).apply()
                _server.value = base; api = candidate; _phase.value = Phase.NeedLogin(); onResult(null)
            } catch (e: NetworkException) {
                onResult("Não foi possível alcançar a API nesse endereço.")
            } catch (e: Exception) {
                onResult("O endereço respondeu, mas não parece ser a API do TalentFlow.")
            }
        }
    }

    fun changeServer() {
        viewModelScope.launch { api?.logout() }
        all.forEach { it.clear() }; details.clear()
        prefs.edit().remove(KEY_BASE).apply(); _server.value = null; api = null
        _phase.value = Phase.NeedServer
    }

    fun login(email: String, password: String, onError: (String) -> Unit) {
        viewModelScope.launch {
            try {
                val user = client().login(email, password)
                _phase.value = Phase.Ready(user); checkVersion(); checkUpdate(force = true)
            } catch (e: ApiException) { onError(e.message ?: "Não foi possível entrar.") }
            catch (e: NetworkException) { onError(e.message ?: "Sem conexão.") }
        }
    }

    fun logout() {
        viewModelScope.launch {
            api?.logout()
            all.forEach { it.clear() }; details.clear()
            _phase.value = Phase.NeedLogin()
        }
    }

    private fun onAuthExpired() {
        all.forEach { it.clear() }
        _phase.value = Phase.NeedLogin("Sua sessão foi encerrada. Entre novamente.")
    }

    private suspend fun checkVersion() {
        try {
            val min = client().health().minClientVersion["android"]
            _notice.value = if (min != null && isVersionBelow(BuildConfig.VERSION_NAME, min))
                "Este aplicativo (${BuildConfig.VERSION_NAME}) está abaixo da versão mínima $min exigida pelo servidor. Baixe a versão mais recente." else null
        } catch (_: Exception) { /* aviso é opcional */ }
    }

    // ---------- atualização do aplicativo ----------
    /** Pergunta ao servidor se há build mais nova (publicada nas Releases do GitHub ou na pasta do servidor). */
    fun checkUpdate(force: Boolean = false, onDone: (String) -> Unit = {}) {
        val s = _update.value
        if (s is UpdateState.Downloading || s is UpdateState.WaitingConfirm) return
        if (!force && System.currentTimeMillis() - lastUpdateCheck < UPDATE_CHECK_MS) return
        viewModelScope.launch {
            try {
                lastUpdateCheck = System.currentTimeMillis()
                // A build de depuração tem o sufixo "-debug" só no nome: comparamos sem ele.
                val info = Updater.check(client(), BuildConfig.VERSION_NAME.removeSuffix("-debug"))
                _update.value = if (info != null) UpdateState.Available(info) else UpdateState.Idle
                onDone(if (info != null) "Versão ${info.version} disponível." else "Você já está na versão mais recente publicada.")
            } catch (_: AuthExpiredException) { onAuthExpired() }
            catch (e: ApiException) { onDone(e.message ?: "Não foi possível verificar.") }
            catch (e: NetworkException) { onDone(e.message ?: "Sem conexão.") }
        }
    }

    /** Baixa, confere o SHA-256 e entrega ao instalador do Android (a pessoa só confirma na tela do sistema). */
    fun startUpdate() {
        val info = when (val s = _update.value) {
            is UpdateState.Available -> s.info; is UpdateState.NeedsPermission -> s.info; is UpdateState.Failed -> s.info; else -> null
        } ?: return
        val ctx = getApplication<Application>()
        if (!UpdateInstaller.canInstall(ctx)) { _update.value = UpdateState.NeedsPermission(info); UpdateInstaller.openPermissionSettings(ctx); return }
        viewModelScope.launch {
            try {
                _update.value = UpdateState.Downloading(info, 0)
                val file = Updater.downloadAndVerify(client(), info, File(ctx.cacheDir, "updates"), "talentflow-update.apk") { n -> _update.value = UpdateState.Downloading(info, n) }
                _update.value = UpdateState.WaitingConfirm(info)
                UpdateInstaller.install(ctx, file)
            } catch (e: UpdateIntegrityException) { _update.value = UpdateState.Failed(info, e.message ?: "Arquivo corrompido.") }
            catch (_: AuthExpiredException) { onAuthExpired() }
            catch (e: ApiException) { _update.value = UpdateState.Failed(info, e.message ?: "Falha ao baixar.") }
            catch (e: NetworkException) { _update.value = UpdateState.Failed(info, e.message ?: "Sem conexão.") }
            catch (e: IOException) { _update.value = UpdateState.Failed(info, "Não foi possível gravar a atualização: ${e.message}") }
            catch (e: SecurityException) { _update.value = UpdateState.Failed(info, "O Android negou a instalação: ${e.message}") }
        }
    }

    // ---------- sincronização ----------
    /** Chamado enquanto o app está visível; cancelado ao ir para segundo plano. */
    suspend fun runSync() {
        val a = api ?: return
        val role = (phase.value as? Phase.Ready)?.user?.role
        if (role == "candidate") { _connection.value = Connection.Online; return }
        val feed = ChangeFeed(a)
        while (true) {
            try {
                val changed = feed.poll()
                _connection.value = Connection.Online
                if (changed.isNotEmpty()) all.filter { it.isActive && it.entities.any(changed::contains) }.forEach { it.refresh() }
            } catch (_: AuthExpiredException) { onAuthExpired(); return }
            catch (e: CancellationException) { throw e }
            catch (_: Exception) { _connection.value = Connection.Offline }
            delay(POLL_MS)
        }
    }

    // ---------- ações ----------
    private suspend fun act(block: suspend () -> Unit): ActionResult = try {
        block(); ActionResult.Success
    } catch (e: ApiException) {
        if (e.isConflict) ActionResult.Conflict(e.message ?: "O registro foi alterado por outra pessoa.") else ActionResult.Failure(e.message ?: "Erro")
    } catch (e: NetworkException) { ActionResult.Failure(e.message ?: "Sem conexão") }
    catch (_: AuthExpiredException) { onAuthExpired(); ActionResult.Failure("Sessão expirada") }

    fun createJob(title: String, department: String, location: String, status: String, done: (ActionResult) -> Unit) {
        viewModelScope.launch { done(act { client().createJob(title, department, location, status) }.also { jobs.refresh() }) }
    }
    fun renameJob(job: Job, title: String, done: (ActionResult) -> Unit) {
        viewModelScope.launch { done(act { client().updateJobTitle(job, title) }.also { jobs.refresh(); details[job.id]?.refresh() }) }
    }
    fun moveApplication(app: ApplicationRow, stageId: Int, reason: String, done: (ActionResult) -> Unit) {
        viewModelScope.launch { done(act { client().moveApplication(app, stageId, reason) }.also { details[app.jobId]?.refresh() }) }
    }
    fun completePlanAction(plan: Plan, index: Int, done: Boolean, evidence: String, result: (ActionResult) -> Unit) {
        viewModelScope.launch { result(act { client().setPlanAction(plan, index, done, evidence) }.also { plans.refresh() }) }
    }
    fun decideLeave(leave: Leave, approved: Boolean, result: (ActionResult) -> Unit) {
        viewModelScope.launch { result(act { client().decideLeave(leave.id, approved) }.also { leaves.refresh() }) }
    }
    fun revokeOtherSessions(result: (String) -> Unit) {
        viewModelScope.launch {
            try { val n = client().revokeOtherSessions(); sessions.refresh(); result("$n outra(s) sessão(ões) encerrada(s).") }
            catch (e: Exception) { result((e as? ApiException)?.message ?: "Não foi possível encerrar as sessões.") }
        }
    }

    val deviceName: String get() = "${Build.MANUFACTURER} ${Build.MODEL}".trim()

    private fun newClient(base: String) = ApiClient(base, tokenStore, "android", deviceName)

    private companion object {
        const val KEY_BASE = "api_base"
        const val POLL_MS = 5000L
        const val UPDATE_CHECK_MS = 30 * 60 * 1000L
    }
}



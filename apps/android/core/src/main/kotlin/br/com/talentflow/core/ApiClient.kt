package br.com.talentflow.core

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl.Companion.toHttpUrl
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.KSerializer
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

data class Tokens(val access: String, val refresh: String)

/** Onde os tokens ficam guardados. No Android: cifrados com chave do Android Keystore. */
interface TokenStore {
    fun load(): Tokens?
    fun save(tokens: Tokens?)
}

class MemoryTokenStore : TokenStore {
    @Volatile private var value: Tokens? = null
    override fun load() = value
    override fun save(tokens: Tokens?) { value = tokens }
}

/**
 * Cliente da API v1. Fala apenas HTTPS com a API (o PostgreSQL nunca é acessado diretamente).
 * - Authorization: Bearer <access>; em 401 faz UM refresh (rotativo) e repete a chamada.
 * - Se o refresh falhar, apaga os tokens e lança [AuthExpiredException].
 * - Mutations usam If-Match com a versão que a pessoa viu; 409 vira [ApiException.isConflict].
 */
class ApiClient(
    val apiBase: String,
    private val store: TokenStore,
    private val clientName: String = "android",
    private val device: String = "",
    private val http: OkHttpClient = defaultHttp(),
) {
    val json = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false }
    private val refreshLock = Mutex()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    val isSignedIn: Boolean get() = store.load() != null

    suspend fun login(email: String, password: String): User {
        val body = buildJsonObject {
            put("email", email.trim()); put("password", password); put("client", clientName); put("device", device)
        }
        val res = execute("POST", "/auth/token", body, null, authenticated = false)
        val parsed = json.decodeFromString(TokenResponse.serializer(), res)
        store.save(Tokens(parsed.accessToken, parsed.refreshToken))
        return parsed.user
    }

    suspend fun logout() {
        try { execute("POST", "/auth/logout", buildJsonObject { }, null, retryOnAuth = false) }
        catch (_: Exception) { /* sair deve sempre limpar o dispositivo, mesmo sem rede */ }
        finally { store.save(null) }
    }

    suspend fun health(): HealthInfo = json.decodeFromString(HealthInfo.serializer(), execute("GET", "/health", null, null, authenticated = false))

    // ---- genéricos ----
    suspend fun <T> get(path: String, ser: KSerializer<T>): T = json.decodeFromString(ser, execute("GET", path, null, null))
    suspend fun <T> list(path: String, ser: KSerializer<T>): List<T> = json.decodeFromString(ListSerializer(ser), execute("GET", path, null, null))
    suspend fun <T> post(path: String, body: JsonObject, ser: KSerializer<T>, ifMatch: Int? = null): T =
        json.decodeFromString(ser, execute("POST", path, body, ifMatch))
    suspend fun <T> patch(path: String, body: JsonObject, ser: KSerializer<T>, ifMatch: Int): T =
        json.decodeFromString(ser, execute("PATCH", path, body, ifMatch))

    /**
     * Baixa um arquivo (caminho da API ou URL absoluta) em streaming. O token só vai para o MESMO servidor da API;
     * URL de outro host exige HTTPS e vai sem credencial.
     */
    suspend fun download(pathOrUrl: String, sink: java.io.OutputStream, onProgress: (Long) -> Unit = {}) {
        val target = when {
            pathOrUrl.startsWith("https://") || pathOrUrl.startsWith("http://") -> pathOrUrl
            pathOrUrl.startsWith("/api/v1/") -> apiBase + pathOrUrl.removePrefix("/api/v1")
            else -> apiBase + (if (pathOrUrl.startsWith("/")) "" else "/") + pathOrUrl
        }
        val base = apiBase.toHttpUrl(); val url = target.toHttpUrl()
        val sameHost = url.scheme == base.scheme && url.host == base.host && url.port == base.port
        if (!sameHost && url.scheme != "https") throw ApiException(400, "Download recusado: endereço de outro servidor precisa de HTTPS.")
        for (attempt in 0..1) {
            val used = if (sameHost) store.load()?.access else null
            val builder = Request.Builder().url(url)
            if (used != null) builder.header("Authorization", "Bearer $used")
            val response = try { withContext(Dispatchers.IO) { http.newCall(builder.build()).execute() } } catch (e: IOException) { throw NetworkException(e) }
            if (response.code == 401 && sameHost && attempt == 0) {
                response.close()
                if (!refresh(used)) throw AuthExpiredException()
                continue
            }
            response.use { r ->
                if (!r.isSuccessful) throw ApiException(r.code, "Falha ao baixar o arquivo (HTTP ${r.code}).")
                withContext(Dispatchers.IO) {
                    r.body!!.byteStream().use { src ->
                        val buffer = ByteArray(64 * 1024); var total = 0L
                        while (true) {
                            val n = src.read(buffer); if (n < 0) break
                            sink.write(buffer, 0, n); total += n; onProgress(total)
                        }
                    }
                }
            }
            return
        }
    }

    // ---- núcleo ----
    internal suspend fun execute(
        method: String, path: String, body: JsonObject?, ifMatch: Int?,
        authenticated: Boolean = true, retryOnAuth: Boolean = true,
    ): String {
        val used = store.load()?.access
        val first = send(method, path, body, ifMatch, if (authenticated) used else null)
        if (first.status == 401 && authenticated && retryOnAuth) {
            if (!refresh(used)) throw AuthExpiredException()
            val second = send(method, path, body, ifMatch, store.load()?.access)
            if (second.status == 401) { store.save(null); throw AuthExpiredException() }
            return unwrap(second)
        }
        return unwrap(first)
    }

    /** Evita refresh em paralelo: quem chegar depois do primeiro reutiliza o novo token. */
    private suspend fun refresh(accessThatFailed: String?): Boolean = refreshLock.withLock {
        val current = store.load() ?: return false
        if (current.access != accessThatFailed) return true // outra chamada já renovou
        val body = buildJsonObject { put("refresh_token", current.refresh) }
        val r = send("POST", "/auth/refresh", body, null, null)
        if (r.status != 200) { store.save(null); return false }
        val parsed = json.decodeFromString(RefreshResponse.serializer(), r.body)
        store.save(Tokens(parsed.accessToken, parsed.refreshToken))
        true
    }

    private class Raw(val status: Int, val body: String)

    private fun unwrap(r: Raw): String {
        if (r.status in 200..299) return r.body
        var detail: JsonElement? = null
        val message = try {
            val root = json.parseToJsonElement(r.body) as? JsonObject
            detail = root?.get("detail")
            when (val d = detail) {
                is JsonPrimitive -> d.contentOrNull
                is JsonObject -> d["message"]?.jsonPrimitive?.contentOrNull
                is JsonArray -> "Revise os campos informados."
                else -> null
            }
        } catch (_: Exception) { null }
        throw ApiException(r.status, message ?: "Erro ${r.status}", detail)
    }

    private suspend fun send(method: String, path: String, body: JsonObject?, ifMatch: Int?, access: String?): Raw {
        val builder = Request.Builder().url(apiBase + path).header("Accept", "application/json")
        if (access != null) builder.header("Authorization", "Bearer $access")
        if (ifMatch != null) builder.header("If-Match", ifMatch.toString())
        val requestBody = body?.let { json.encodeToString(JsonObject.serializer(), it).toRequestBody(jsonType) }
        builder.method(method, requestBody ?: if (method == "GET") null else "".toRequestBody(jsonType))
        val call = http.newCall(builder.build())
        return suspendCancellableCoroutine { cont ->
            cont.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) { if (!cont.isCompleted) cont.resumeWithException(NetworkException(e)) }
                override fun onResponse(call: Call, response: Response) {
                    response.use { cont.resume(Raw(it.code, it.body?.string().orEmpty())) }
                }
            })
        }
    }

    companion object {
        fun defaultHttp(): OkHttpClient = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).writeTimeout(20, TimeUnit.SECONDS)
            .build()
    }
}

// ---- operações de domínio (mesmos endpoints do site e do Windows) ----
suspend fun ApiClient.dashboard() = get("/dashboard", Dashboard.serializer())
suspend fun ApiClient.trend() = get("/dashboard/trend", Trend.serializer())
suspend fun ApiClient.updateInfo(platform: String = "android") = get("/client-updates/$platform", UpdateInfo.serializer())
suspend fun ApiClient.insights() = get("/workforce/insights", Insights.serializer())
suspend fun ApiClient.jobs(query: String = "") = list("/jobs?q=${java.net.URLEncoder.encode(query, "UTF-8")}", Job.serializer())
suspend fun ApiClient.jobDetail(id: Int) = get("/jobs/$id", JobDetail.serializer())
suspend fun ApiClient.createJob(title: String, department: String, location: String, status: String): Job =
    post("/jobs", buildJsonObject {
        put("title", title)
        if (department.isNotBlank()) put("department", department)
        if (location.isNotBlank()) put("location", location)
        put("status", status)
    }, Job.serializer())
suspend fun ApiClient.updateJobTitle(job: Job, title: String): Job =
    patch("/jobs/${job.id}", buildJsonObject { put("title", title) }, Job.serializer(), job.version)
suspend fun ApiClient.moveApplication(app: ApplicationRow, stageId: Int, reason: String = ""): MoveResult =
    post("/applications/${app.id}/move", buildJsonObject { put("stage_id", stageId); put("reason", reason) }, MoveResult.serializer(), app.version)
suspend fun ApiClient.candidates(query: String = "") = list("/candidates?q=${java.net.URLEncoder.encode(query, "UTF-8")}", Candidate.serializer())
suspend fun ApiClient.employees() = list("/lifecycle/employees", Employee.serializer())
suspend fun ApiClient.plans(status: String = "active") = list("/workforce/plans?status=$status", Plan.serializer())
suspend fun ApiClient.setPlanAction(plan: Plan, index: Int, done: Boolean, evidence: String = ""): Plan =
    post("/workforce/plans/${plan.id}/action", buildJsonObject { put("index", index); put("done", done); put("evidence", evidence) }, Plan.serializer(), plan.version)
suspend fun ApiClient.leaves(status: String = "") = list("/workforce/leaves?status=$status", Leave.serializer())
suspend fun ApiClient.decideLeave(id: Int, approved: Boolean): Leave =
    post("/workforce/leaves/$id/decide", buildJsonObject { put("decision", if (approved) "approved" else "rejected") }, Leave.serializer())
suspend fun ApiClient.me(): User = get("/me", MeEnvelope.serializer()).user
suspend fun ApiClient.portal() = get("/portal", Portal.serializer())
suspend fun ApiClient.sessions() = list("/auth/sessions", SessionInfo.serializer())
suspend fun ApiClient.revokeOtherSessions(): Int =
    json.parseToJsonElement(execute("POST", "/auth/sessions/revoke-others", buildJsonObject { }, null)).let { (it as JsonObject)["revoked"]!!.jsonPrimitive.content.toInt() }

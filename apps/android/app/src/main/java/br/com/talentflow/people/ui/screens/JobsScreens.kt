package br.com.talentflow.people.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import br.com.talentflow.core.ApplicationRow
import br.com.talentflow.core.Job
import br.com.talentflow.core.Stage
import br.com.talentflow.core.User
import br.com.talentflow.people.data.ActionResult
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.ui.Banner
import br.com.talentflow.people.ui.ConflictDialog
import br.com.talentflow.people.ui.EmptyState
import br.com.talentflow.people.ui.ScreenHeader
import br.com.talentflow.people.ui.StateView
import br.com.talentflow.people.ui.Tag
import br.com.talentflow.people.ui.Tone
import br.com.talentflow.people.ui.rememberLoad

private fun jobStatus(s: String): Pair<String, Tone> = when (s) {
    "open" -> "Aberta" to Tone.Positive
    "approval" -> "Em aprovação" to Tone.Attention
    "closed" -> "Encerrada" to Tone.Neutral
    else -> "Arquivada" to Tone.Neutral
}

private fun canEdit(user: User) = user.role == "admin" || user.role == "recruiter"

@Composable
fun JobsScreen(vm: AppViewModel, user: User, onOpen: (Int) -> Unit) {
    val load = rememberLoad(vm.jobs)
    var query by rememberSaveable { mutableStateOf("") }
    var creating by rememberSaveable { mutableStateOf(false) }
    val listState = rememberLazyListState()
    // A lista vem do mais novo para o mais antigo. O LazyColumn "segue" o item que estava no topo pela chave,
    // então uma vaga nova (nossa ou criada por outro cliente) entrava ACIMA da área visível e ficava escondida.
    // Quem estava no topo continua vendo o topo; quem rolou para baixo não é puxado de volta.
    var pinnedToTop by remember { mutableStateOf(true) }
    LaunchedEffect(listState) {
        snapshotFlow { listState.isScrollInProgress }.collect { moving ->
            if (!moving) pinnedToTop = listState.firstVisibleItemIndex == 0 && listState.firstVisibleItemScrollOffset == 0
        }
    }
    Column(Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        ScreenHeader("Recrutamento", "Vagas", "Requisições e vagas com seus pipelines.") {
            if (canEdit(user)) Button(onClick = { creating = true }) { Text("Nova vaga") }
        }
        OutlinedTextField(query, { query = it }, label = { Text("Buscar por título") }, singleLine = true, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        StateView(load, onRetry = { vm.jobs.refresh() }) { all ->
            val jobs = all.filter { it.title.contains(query, ignoreCase = true) }
            if (jobs.isEmpty()) EmptyState("Nenhuma vaga encontrada", if (canEdit(user)) "Crie a primeira vaga para iniciar um processo seletivo." else "Não há vagas atribuídas a você.")
            else {
                val topId = jobs.first().id
                LaunchedEffect(topId) { if (pinnedToTop) listState.requestScrollToItem(0) }
                LazyColumn(state = listState, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(jobs, key = { it.id }) { job -> JobRow(job) { onOpen(job.id) } }
                }
            }
        }
    }
    if (creating) NewJobDialog(vm, onCreated = { pinnedToTop = true }, onDismiss = { creating = false })
}

@Composable
private fun JobRow(job: Job, onClick: () -> Unit) {
    val (label, tone) = jobStatus(job.status)
    Surface(shape = RoundedCornerShape(18.dp), color = MaterialTheme.colorScheme.surface, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant), modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(job.code, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Tag(label, tone)
            }
            Text(job.title, style = MaterialTheme.typography.titleMedium)
            Text("${job.department} · ${job.location} · ${job.applications} candidatura(s)", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun NewJobDialog(vm: AppViewModel, onCreated: () -> Unit, onDismiss: () -> Unit) {
    var title by rememberSaveable { mutableStateOf("") }
    var dept by rememberSaveable { mutableStateOf("") }
    var place by rememberSaveable { mutableStateOf("") }
    var status by rememberSaveable { mutableStateOf("approval") }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    var busy by rememberSaveable { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = { if (!busy) onDismiss() },
        title = { Text("Nova vaga") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (error != null) Banner(error!!, Tone.Critical)
                OutlinedTextField(title, { title = it }, label = { Text("Título da vaga") }, singleLine = true)
                OutlinedTextField(dept, { dept = it }, label = { Text("Área") }, singleLine = true)
                OutlinedTextField(place, { place = it }, label = { Text("Local") }, singleLine = true)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(status == "approval", { status = "approval" }, label = { Text("Em aprovação") })
                    FilterChip(status == "open", { status = "open" }, label = { Text("Aberta") })
                }
            }
        },
        confirmButton = {
            Button(enabled = !busy && title.trim().length >= 3, onClick = {
                busy = true; error = null
                vm.createJob(title.trim(), dept.trim(), place.trim(), status) { r ->
                    busy = false
                    when (r) { is ActionResult.Success -> { onCreated(); onDismiss() }; is ActionResult.Failure -> error = r.message; is ActionResult.Conflict -> error = r.message }
                }
            }) { Text(if (busy) "Salvando…" else "Criar vaga") }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
fun JobDetailScreen(vm: AppViewModel, user: User, jobId: Int, onBack: () -> Unit) {
    val resource = remember(jobId) { vm.jobDetail(jobId) }
    val load = rememberLoad(resource)
    var stageIndex by rememberSaveable { mutableStateOf(0) }
    var message by remember { mutableStateOf<String?>(null) }
    var conflict by remember { mutableStateOf<String?>(null) }
    var finalMove by remember { mutableStateOf<Pair<ApplicationRow, Stage>?>(null) }
    var editing by remember { mutableStateOf<Job?>(null) }

    fun handle(r: ActionResult, ok: String) {
        when (r) {
            is ActionResult.Success -> message = ok
            is ActionResult.Conflict -> { conflict = r.message; resource.refresh() }
            is ActionResult.Failure -> message = r.message
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        TextButton(onClick = onBack) { Text("‹ Vagas") }
        StateView(load, onRetry = { resource.refresh() }) { detail ->
            val (label, tone) = jobStatus(detail.job.status)
            ScreenHeader(detail.job.code, detail.job.title, "${detail.job.department} · ${detail.job.location} · versão ${detail.job.version}") {
                Tag(label, tone)
            }
            if (canEdit(user)) OutlinedButton(onClick = { editing = detail.job }) { Text("Editar título") }
            if (message != null) { Spacer(Modifier.height(8.dp)); Banner(message!!, Tone.Info) }
            if (detail.applications.isEmpty()) { Spacer(Modifier.height(12.dp)); EmptyState("Nenhuma candidatura nesta vaga") }
            else {
                val index = stageIndex.coerceIn(0, detail.stages.lastIndex)
                androidx.compose.foundation.lazy.LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(vertical = 8.dp)) {
                    items(detail.stages.size) { i ->
                        val s = detail.stages[i]; val n = detail.applications.count { it.stageId == s.id }
                        FilterChip(index == i, { stageIndex = i }, label = { Text("${s.name} · $n") })
                    }
                }
                val stage = detail.stages[index]
                val inStage = detail.applications.filter { it.stageId == stage.id }
                if (inStage.isEmpty()) EmptyState("Ninguém nesta etapa")
                else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(inStage, key = { it.id }) { app ->
                        ApplicationCard(app, detail.stages, canMove = canEdit(user) || user.role == "manager") { target ->
                            if (target.kind != "active") finalMove = app to target
                            else vm.moveApplication(app, target.id, "") { handle(it, "${app.candidate.name} movido para ${target.name}.") }
                        }
                    }
                }
            }
        }
    }

    finalMove?.let { (app, target) ->
        var reason by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { finalMove = null },
            title = { Text(if (target.kind == "hired") "Registrar contratação" else "Registrar reprovação") },
            text = { Column { Text("Decisões finais exigem um motivo, que fica no histórico e na auditoria.")
                OutlinedTextField(reason, { reason = it }, label = { Text("Motivo para ${app.candidate.name}") }) } },
            confirmButton = { Button(enabled = reason.trim().length >= 3, onClick = {
                finalMove = null
                vm.moveApplication(app, target.id, reason.trim()) { handle(it, "${app.candidate.name} movido para ${target.name}.") }
            }) { Text("Confirmar") } },
            dismissButton = { TextButton(onClick = { finalMove = null }) { Text("Cancelar") } },
        )
    }
    editing?.let { snapshot ->
        // O título editado fica preso à VERSÃO em que o diálogo foi aberto (snapshot): se outra pessoa salvar antes, vem 409.
        var title by remember(snapshot.version) { mutableStateOf(snapshot.title) }
        AlertDialog(
            onDismissRequest = { editing = null },
            title = { Text("Editar vaga") },
            text = { OutlinedTextField(title, { title = it }, label = { Text("Título") }, singleLine = true) },
            confirmButton = { Button(enabled = title.trim().length >= 3, onClick = {
                editing = null
                vm.renameJob(snapshot, title.trim()) { handle(it, "Vaga atualizada.") }
            }) { Text("Salvar") } },
            dismissButton = { TextButton(onClick = { editing = null }) { Text("Cancelar") } },
        )
    }
    conflict?.let { ConflictDialog(it, onReload = { resource.refresh() }, onDismiss = { conflict = null }) }
}

@Composable
private fun ApplicationCard(app: ApplicationRow, stages: List<Stage>, canMove: Boolean, onMove: (Stage) -> Unit) {
    var menu by remember { mutableStateOf(false) }
    Surface(shape = RoundedCornerShape(18.dp), color = MaterialTheme.colorScheme.surface, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(app.candidate.name, style = MaterialTheme.typography.titleMedium)
            Text(app.candidate.title.ifBlank { app.candidate.location.ifBlank { "—" } }, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Tag("Fit ${if (app.fit >= 75) "alto" else if (app.fit >= 50) "médio" else "baixo"} · ${app.fit}", if (app.fit >= 75) Tone.Positive else if (app.fit >= 50) Tone.Info else Tone.Neutral)
                if (canMove) {
                    androidx.compose.foundation.layout.Box {
                        OutlinedButton(onClick = { menu = true }) { Text("Mover para…") }
                        DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                            stages.filter { it.id != app.stageId }.forEach { s -> DropdownMenuItem(text = { Text(s.name) }, onClick = { menu = false; onMove(s) }) }
                        }
                    }
                }
            }
        }
    }
}

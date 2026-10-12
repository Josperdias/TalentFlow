package br.com.talentflow.people.ui.screens

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import br.com.talentflow.core.Plan
import br.com.talentflow.core.User
import br.com.talentflow.people.BuildConfig
import br.com.talentflow.people.data.ActionResult
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.ui.Banner
import br.com.talentflow.people.ui.ConflictDialog
import br.com.talentflow.people.ui.EmptyState
import br.com.talentflow.people.ui.Eyebrow
import br.com.talentflow.people.ui.ScreenHeader
import br.com.talentflow.people.ui.StateView
import br.com.talentflow.people.ui.Tag
import br.com.talentflow.people.ui.Tone
import br.com.talentflow.people.ui.rememberLoad

@Composable
private fun CardBox(content: @Composable () -> Unit) =
    Surface(shape = RoundedCornerShape(18.dp), color = MaterialTheme.colorScheme.surface, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) { content() }
    }

@Composable
fun CandidatesScreen(vm: AppViewModel) {
    val load = rememberLoad(vm.candidates)
    var query by rememberSaveable { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        ScreenHeader("Recrutamento", "Candidatos", "Você só vê pessoas ligadas às vagas que pode acessar.")
        OutlinedTextField(query, { query = it }, label = { Text("Buscar por nome, cargo ou habilidade") }, singleLine = true, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        StateView(load, onRetry = { vm.candidates.refresh() }) { all ->
            val list = all.filter { c -> listOf(c.name, c.title, c.skills).any { it.contains(query, ignoreCase = true) } }
            if (list.isEmpty()) EmptyState("Nenhum candidato encontrado")
            else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(list, key = { it.id }) { c ->
                    CardBox {
                        Text(c.name, style = MaterialTheme.typography.titleMedium)
                        Text(listOf(c.title, c.location).filter { it.isNotBlank() }.joinToString(" · ").ifBlank { "—" }, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text("${c.source} · ${c.experienceYears} ano(s) de experiência", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

@Composable
fun PeopleScreen(vm: AppViewModel, user: User) {
    var tab by rememberSaveable { mutableIntStateOf(0) }
    val tabs = listOf("Colaboradores", "Desenvolvimento", "Ausências")
    Column(Modifier.fillMaxSize()) {
        Column(Modifier.padding(horizontal = 16.dp)) { ScreenHeader("Pessoas", tabs[tab]) }
        TabRow(selectedTabIndex = tab, containerColor = MaterialTheme.colorScheme.background) {
            tabs.forEachIndexed { i, t -> Tab(selected = tab == i, onClick = { tab = i }, text = { Text(t, maxLines = 1) }) }
        }
        Column(Modifier.fillMaxSize().padding(16.dp)) {
            when (tab) { 0 -> Employees(vm); 1 -> Plans(vm); else -> Leaves(vm, user) }
        }
    }
}

@Composable
private fun Employees(vm: AppViewModel) {
    val load = rememberLoad(vm.employees)
    StateView(load, onRetry = { vm.employees.refresh() }) { list ->
        if (list.isEmpty()) EmptyState("Nenhum colaborador encontrado")
        else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(list, key = { it.id }) { e ->
                CardBox {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(e.employeeCode, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Tag(if (e.status == "active") "Ativo" else "Desligado", if (e.status == "active") Tone.Positive else Tone.Neutral)
                    }
                    Text(e.name, style = MaterialTheme.typography.titleMedium)
                    Text("${e.jobTitle.ifBlank { "—" }} · ${e.department}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable
private fun Plans(vm: AppViewModel) {
    val load = rememberLoad(vm.plans)
    var conflict by remember { mutableStateOf<String?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var pending by remember { mutableStateOf<Pair<Plan, Int>?>(null) }

    fun handle(r: ActionResult) {
        when (r) { is ActionResult.Success -> message = null; is ActionResult.Conflict -> { conflict = r.message; vm.plans.refresh() }; is ActionResult.Failure -> message = r.message }
    }
    Column {
        if (message != null) Banner(message!!, Tone.Critical)
        Text("O progresso mede execução das atividades, não ganho de competência.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(8.dp))
        StateView(load, onRetry = { vm.plans.refresh() }) { plans ->
            if (plans.isEmpty()) EmptyState("Nenhum plano de desenvolvimento")
            else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(plans, key = { it.id }) { p ->
                    CardBox {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(p.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                            Tag(if (p.status == "completed") "Concluído" else "Em andamento", if (p.status == "completed") Tone.Positive else Tone.Info)
                        }
                        Text("${p.employee} · prazo ${p.dueDate}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        LinearProgressIndicator(progress = { p.progress / 100f }, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp))
                        p.actions.forEachIndexed { i, a ->
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Checkbox(checked = a.done, enabled = p.status != "archived", onCheckedChange = { checked ->
                                    if (checked) pending = p to i else vm.completePlanAction(p, i, false, "") { handle(it) }
                                })
                                Column { Text(a.title, style = MaterialTheme.typography.bodyMedium)
                                    if (a.evidence.isNotBlank()) Text(a.evidence, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                            }
                        }
                    }
                }
            }
        }
    }
    pending?.let { (plan, index) ->
        var evidence by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { pending = null },
            title = { Text("Concluir atividade") },
            text = { Column { Text(plan.actions[index].title); OutlinedTextField(evidence, { evidence = it }, label = { Text("Evidência (opcional)") }) } },
            confirmButton = { Button(onClick = { pending = null; vm.completePlanAction(plan, index, true, evidence.trim()) { handle(it) } }) { Text("Marcar como concluída") } },
            dismissButton = { TextButton(onClick = { pending = null }) { Text("Cancelar") } },
        )
    }
    conflict?.let { ConflictDialog(it, onReload = { vm.plans.refresh() }, onDismiss = { conflict = null }) }
}

@Composable
private fun Leaves(vm: AppViewModel, user: User) {
    val load = rememberLoad(vm.leaves)
    var message by remember { mutableStateOf<String?>(null) }
    val canDecide = user.role == "admin" || user.role == "manager"
    val kinds = mapOf("vacation" to "Férias", "personal" to "Pessoal", "medical" to "Saúde", "other" to "Outro")
    Column {
        if (message != null) Banner(message!!, Tone.Critical)
        StateView(load, onRetry = { vm.leaves.refresh() }) { list ->
            if (list.isEmpty()) EmptyState("Nenhuma solicitação")
            else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(list, key = { it.id }) { l ->
                    CardBox {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(l.employee, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                            when (l.status) { "approved" -> Tag("Aprovada", Tone.Positive); "rejected" -> Tag("Recusada", Tone.Critical); else -> Tag("Pendente", Tone.Attention) }
                        }
                        Text("${kinds[l.kind] ?: l.kind} · ${l.startsOn} a ${l.endsOn} · ${l.days} dia(s)", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        if (l.status == "pending" && canDecide) Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(onClick = { vm.decideLeave(l, false) { r -> message = (r as? ActionResult.Failure)?.message } }) { Text("Recusar") }
                            Button(onClick = { vm.decideLeave(l, true) { r -> message = (r as? ActionResult.Failure)?.message } }) { Text("Aprovar") }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun PortalScreen(vm: AppViewModel) {
    val load = rememberLoad(vm.portal)
    Column(Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        ScreenHeader("Candidatura", "Minhas candidaturas", "Acompanhe em que etapa está cada processo seletivo.")
        StateView(load, onRetry = { vm.portal.refresh() }) { portal ->
            if (portal.applications.isEmpty()) EmptyState("Nenhuma candidatura encontrada", "Candidaturas feitas com este e-mail aparecem aqui.")
            else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(portal.applications, key = { it.id }) { a ->
                    CardBox {
                        Text(a.job, style = MaterialTheme.typography.titleMedium)
                        Text(a.company, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Tag(a.stage)
                        if (a.interviews.isNotEmpty()) Text("Entrevistas: " + a.interviews.joinToString { it.startsAt.take(16).replace('T', ' ') }, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
fun AccountScreen(vm: AppViewModel, user: User) {
    val sessions = rememberLoad(vm.sessions)
    val server by vm.server.collectAsState()
    var message by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        ScreenHeader("Conta", user.name, "${user.email} · ${user.company}")
        if (message != null) Banner(message!!, Tone.Info)
        Eyebrow("Aplicativo", Modifier.padding(top = 4.dp))
        Text("TalentFlow People ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.bodyMedium)
        Text(server ?: "", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = { vm.checkUpdate(force = true) { message = it } }) { Text("Verificar atualizações") }
        Eyebrow("Sessões ativas")
        StateView(sessions, onRetry = { vm.sessions.refresh() }) { list ->
            list.forEach { s ->
                Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("${s.client} · ${if (s.kind == "cookie") "navegador" else "aplicativo"}", style = MaterialTheme.typography.bodyMedium)
                    if (s.current) Tag("Esta sessão", Tone.Info)
                }
            }
        }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = { vm.revokeOtherSessions { message = it } }) { Text("Encerrar as outras sessões") }
        Spacer(Modifier.height(16.dp))
        Button(onClick = { vm.logout() }, modifier = Modifier.fillMaxWidth().height(48.dp)) { Text("Sair") }
        TextButton(onClick = { vm.changeServer() }) { Text("Trocar de servidor") }
    }
}


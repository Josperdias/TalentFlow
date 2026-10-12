package br.com.talentflow.people.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Surface
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.repeatOnLifecycle
import br.com.talentflow.core.User
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.data.Connection
import br.com.talentflow.people.data.Phase
import br.com.talentflow.people.ui.screens.AccountScreen
import br.com.talentflow.people.ui.screens.CandidatesScreen
import br.com.talentflow.people.ui.screens.JobDetailScreen
import br.com.talentflow.people.ui.screens.JobsScreen
import br.com.talentflow.people.ui.screens.OverviewScreen
import br.com.talentflow.people.ui.screens.PeopleScreen
import br.com.talentflow.people.ui.screens.PortalScreen
import br.com.talentflow.people.ui.theme.LocalTf

@Composable
fun TalentFlowRoot(vm: AppViewModel) {
    val phase by vm.phase.collectAsState()
    Box(Modifier.fillMaxSize().safeDrawingPadding()) {
        when (val p = phase) {
            Phase.Boot -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            Phase.NeedServer -> ServerScreen(vm)
            is Phase.NeedLogin -> LoginScreen(vm, p.message)
            is Phase.Unreachable -> FullScreenMessage("Sem conexão com o servidor", p.message) {
                Button(onClick = { vm.boot() }) { Text("Tentar novamente") }
                TextButton(onClick = { vm.changeServer() }) { Text("Alterar servidor") }
            }
            is Phase.Ready -> MainScaffold(vm, p.user)
        }
    }
}

/** Fundo do acesso: navy com duas "luzes" violeta que derivam devagar (decoração; some com animações desligadas). */
@Composable
private fun AuthBackdrop() {
    val drift = rememberInfiniteTransition(label = "drift")
    val t by drift.animateFloat(0f, 1f, infiniteRepeatable(tween(14000, easing = LinearEasing), RepeatMode.Reverse), label = "t")
    Canvas(Modifier.fillMaxSize()) {
        drawRect(Brush.linearGradient(listOf(Color(0xFF0B1230), Color(0xFF151D4F)), Offset.Zero, Offset(size.width, size.height)))
        drawCircle(Brush.radialGradient(listOf(Color(0x995846D4), Color.Transparent), Offset(size.width * (0.15f + 0.2f * t), size.height * 0.22f), size.width * 0.7f),
            radius = size.width * 0.7f, center = Offset(size.width * (0.15f + 0.2f * t), size.height * 0.22f))
        drawCircle(Brush.radialGradient(listOf(Color(0x80B27BF5), Color.Transparent), Offset(size.width * (0.95f - 0.2f * t), size.height * 0.92f), size.width * 0.8f),
            radius = size.width * 0.8f, center = Offset(size.width * (0.95f - 0.2f * t), size.height * 0.92f))
    }
}

@Composable
private fun AuthFrame(title: String, content: @Composable () -> Unit) {
    Box(Modifier.fillMaxSize()) {
        AuthBackdrop()
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement = Arrangement.Center) {
            Text("TALENTFLOW PEOPLE", style = MaterialTheme.typography.labelSmall, color = Color(0xFFCFC6FF), modifier = Modifier.riseIn())
            Spacer(Modifier.height(10.dp))
            Text("Pessoas, da vaga à carreira, em um só registro.", style = MaterialTheme.typography.headlineSmall, color = Color.White, modifier = Modifier.riseIn(80))
            Spacer(Modifier.height(24.dp))
            Surface(shape = RoundedCornerShape(28.dp), color = MaterialTheme.colorScheme.surface, shadowElevation = 16.dp, modifier = Modifier.fillMaxWidth().riseIn(160)) {
                Column(Modifier.padding(24.dp)) {
                    Text(title, style = MaterialTheme.typography.headlineMedium)
                    Spacer(Modifier.height(18.dp))
                    content()
                }
            }
        }
    }
}

@Composable
private fun ServerScreen(vm: AppViewModel) {
    var address by rememberSaveable { mutableStateOf("") }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    var busy by rememberSaveable { mutableStateOf(false) }
    AuthFrame("Conectar ao servidor") {
        Text("Informe o endereço do TalentFlow da sua empresa, o mesmo do site (por exemplo rh.suaempresa.com.br).",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(address, { address = it }, label = { Text("Endereço do servidor") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri), isError = error != null)
        if (error != null) Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(16.dp))
        GradientButton(if (busy) "Verificando…" else "Continuar", enabled = !busy && address.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
            busy = true; error = null; vm.setServer(address) { e -> busy = false; error = e }
        }
    }
}

@Composable
private fun LoginScreen(vm: AppViewModel, message: String?) {
    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var error by rememberSaveable { mutableStateOf(message) }
    var busy by rememberSaveable { mutableStateOf(false) }
    val server by vm.server.collectAsState()
    AuthFrame("Entrar") {
        if (error != null) { Banner(error!!, Tone.Critical) }
        OutlinedTextField(email, { email = it }, label = { Text("E-mail") }, singleLine = true, modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(password, { password = it }, label = { Text("Senha") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
            visualTransformation = PasswordVisualTransformation(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password))
        Spacer(Modifier.height(16.dp))
        GradientButton(if (busy) "Entrando…" else "Entrar", enabled = !busy && email.isNotBlank() && password.isNotEmpty(), modifier = Modifier.fillMaxWidth()) {
            busy = true; error = null; vm.login(email, password) { e -> busy = false; error = e }
        }
        Spacer(Modifier.height(8.dp))
        Text(server ?: "", style = MaterialTheme.typography.bodySmall, color = LocalTf.current.inkFaint)
        TextButton(onClick = { vm.changeServer() }) { Text("Alterar servidor") }
    }
}

private data class NavItem(val route: String, val label: String, val icon: ImageVector)

private fun navFor(role: String): List<NavItem> = if (role == "candidate") listOf(
    NavItem("portal", "Candidaturas", Icons.AutoMirrored.Filled.List), NavItem("account", "Conta", Icons.Filled.AccountCircle),
) else buildList {
    add(NavItem("overview", "Início", Icons.Filled.Home))
    add(NavItem("jobs", "Vagas", Icons.AutoMirrored.Filled.List))
    add(NavItem("candidates", "Candidatos", Icons.Filled.Person))
    if (role != "interviewer") add(NavItem("people", "Pessoas", Icons.Filled.Face))
    add(NavItem("account", "Conta", Icons.Filled.AccountCircle))
}

@Composable
private fun MainScaffold(vm: AppViewModel, user: User) {
    val items = navFor(user.role)
    var route by rememberSaveable { mutableStateOf(items.first().route) }
    var openJob by rememberSaveable { mutableStateOf<Int?>(null) }
    val connection by vm.connection.collectAsState()
    val notice by vm.notice.collectAsState()
    val lifecycle = LocalLifecycleOwner.current.lifecycle

    // Sincroniza só enquanto o app está visível; ao voltar do segundo plano o feed é retomado.
    LaunchedEffect(user.id) { lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) { vm.runSync() } }
    BackHandler(enabled = openJob != null) { openJob = null }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            val tf = LocalTf.current
            Box(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp)) {
                Surface(shape = RoundedCornerShape(28.dp), color = tf.nav, shadowElevation = 14.dp, border = BorderStroke(1.dp, tf.navLine)) {
                    NavigationBar(containerColor = Color.Transparent, windowInsets = WindowInsets(0, 0, 0, 0)) {
                        items.forEach { item ->
                            NavigationBarItem(selected = route == item.route, onClick = { route = item.route; openJob = null },
                                icon = { Icon(item.icon, contentDescription = null) }, label = { Text(item.label, maxLines = 1) },
                                colors = NavigationBarItemDefaults.colors(
                                    selectedIconColor = tf.navActiveInk, selectedTextColor = tf.navActiveInk, indicatorColor = tf.navActive,
                                    unselectedIconColor = tf.navMuted, unselectedTextColor = tf.navMuted,
                                ))
                        }
                    }
                }
            }
        },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                val color = when (connection) { Connection.Online -> LocalTf.current.positive; Connection.Offline -> LocalTf.current.critical; Connection.Connecting -> LocalTf.current.inkFaint }
                Surface(shape = CircleShape, color = MaterialTheme.colorScheme.surface, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant), shadowElevation = 1.dp) {
                    Row(Modifier.padding(horizontal = 12.dp, vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                        Canvas(Modifier.size(8.dp)) { drawCircle(color) }
                        Spacer(Modifier.size(8.dp))
                        Text(when (connection) { Connection.Online -> "Sincronizado"; Connection.Offline -> "Sem conexão com o servidor"; Connection.Connecting -> "Conectando…" },
                            style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                Spacer(Modifier.weight(1f))
                Text(user.company, style = MaterialTheme.typography.bodySmall, color = LocalTf.current.inkFaint)
                Spacer(Modifier.size(8.dp))
                Avatar(user.name, 32)
            }
            if (notice != null) Box(Modifier.padding(horizontal = 16.dp)) { Banner(notice!!) }
            Box(Modifier.weight(1f).fillMaxWidth()) {
                val job = openJob
                when {
                    job != null -> JobDetailScreen(vm, user, job) { openJob = null }
                    route == "overview" -> OverviewScreen(vm, user)
                    route == "jobs" -> JobsScreen(vm, user) { openJob = it }
                    route == "candidates" -> CandidatesScreen(vm)
                    route == "people" -> PeopleScreen(vm, user)
                    route == "portal" -> PortalScreen(vm)
                    else -> AccountScreen(vm, user)
                }
            }
        }
    }
}

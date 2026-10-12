package br.com.talentflow.people.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import br.com.talentflow.people.data.Load
import br.com.talentflow.people.ui.theme.LocalTf

enum class Tone { Neutral, Positive, Attention, Critical, Info }

/** Selo retangular (não pílula), como no site. */
@Composable
fun Tag(text: String, tone: Tone = Tone.Neutral) {
    val tf = LocalTf
    val (fg, bg) = when (tone) {
        Tone.Neutral -> tf.inkMuted to tf.sunken
        Tone.Positive -> tf.positive to tf.positiveSoft
        Tone.Attention -> tf.attention to tf.attentionSoft
        Tone.Critical -> tf.critical to tf.criticalSoft
        Tone.Info -> tf.info to tf.infoSoft
    }
    Surface(color = bg, contentColor = fg, shape = RoundedCornerShape(2.dp), border = BorderStroke(1.dp, fg.copy(alpha = 0.55f))) {
        Text(text, style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 7.dp, vertical = 1.dp))
    }
}

/** Cabeçalho de tela: rótulo em mono, título em serifa e linha de apoio. */
@Composable
fun ScreenHeader(eyebrow: String, title: String, lead: String? = null, trailing: @Composable (() -> Unit)? = null) {
    Column(Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.SpaceBetween) {
            Column(Modifier.weight(1f)) {
                Text(eyebrow.uppercase(), style = MaterialTheme.typography.labelSmall, color = LocalTf.inkFaint)
                Spacer(Modifier.height(4.dp))
                Text(title, style = MaterialTheme.typography.headlineMedium)
            }
            trailing?.invoke()
        }
        if (lead != null) { Spacer(Modifier.height(4.dp)); Text(lead, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Spacer(Modifier.height(12.dp)); HorizontalDivider()
    }
}

/** Linha de livro-razão: rótulo e nota à esquerda, número em serifa à direita. */
@Composable
fun LedgerRow(label: String, note: String, figure: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 10.dp, horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            Text(note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text(figure, style = MaterialTheme.typography.headlineSmall, textAlign = TextAlign.End)
    }
}

@Composable
fun Ledger(content: @Composable () -> Unit) {
    Surface(color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(4.dp), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
        Column { content() }
    }
}

@Composable
fun Eyebrow(text: String, modifier: Modifier = Modifier) =
    Text(text.uppercase(), style = MaterialTheme.typography.labelSmall, color = LocalTf.inkFaint, modifier = modifier.padding(top = 20.dp, bottom = 8.dp))

@Composable
fun Banner(text: String, tone: Tone = Tone.Attention) {
    val tf = LocalTf
    val (fg, bg) = when (tone) {
        Tone.Critical -> tf.critical to tf.criticalSoft
        Tone.Info -> tf.info to tf.infoSoft
        else -> tf.attention to tf.attentionSoft
    }
    Surface(color = bg, shape = RoundedCornerShape(4.dp), border = BorderStroke(1.dp, fg), modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
        Text(text, color = MaterialTheme.colorScheme.onSurface, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(12.dp))
    }
}

/** Estados de carregamento / erro / sem permissão / dados desatualizados, iguais em todas as telas. */
@Composable
fun <T> StateView(load: Load<T>, onRetry: () -> Unit, content: @Composable (T) -> Unit) {
    when (load) {
        is Load.Idle, is Load.Loading -> Box(Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        is Load.Failed -> Column(Modifier.fillMaxWidth().padding(vertical = 16.dp)) {
            Banner(if (load.forbidden) "Sem permissão para ver esta área. ${load.message}" else load.message, if (load.forbidden) Tone.Attention else Tone.Critical)
            if (!load.forbidden) OutlinedButton(onClick = onRetry) { Text("Tentar novamente") }
        }
        is Load.Ready -> Column {
            if (load.stale) Banner("Sem conexão com o servidor. Os dados abaixo podem estar desatualizados.")
            content(load.data)
        }
    }
}

@Composable
fun EmptyState(title: String, text: String = "") {
    Surface(border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline), shape = RoundedCornerShape(4.dp), color = Color.Transparent, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            if (text.isNotEmpty()) Text(text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        }
    }
}

/** Mostrado quando outro cliente salvou antes (HTTP 409). Nada foi sobrescrito. */
@Composable
fun ConflictDialog(message: String, onReload: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Registro alterado por outra pessoa") },
        text = { Text("$message\n\nSuas alterações não foram salvas. Carregue a versão atual, revise e edite novamente.") },
        confirmButton = { Button(onClick = { onReload(); onDismiss() }) { Text("Carregar versão atual") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Fechar") } },
    )
}

@Composable
fun Rule() = HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

@Composable
fun FullScreenMessage(title: String, text: String, action: @Composable () -> Unit) {
    Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(24.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, style = MaterialTheme.typography.headlineSmall, textAlign = TextAlign.Center)
            Spacer(Modifier.height(8.dp))
            Text(text, style = MaterialTheme.typography.bodyMedium, textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(16.dp)); action()
        }
    }
}

/** Liga a tela ao recurso: dispara a primeira carga e acompanha o estado. */
@Composable
fun <T> rememberLoad(resource: br.com.talentflow.people.data.Loadable<T>): Load<T> {
    androidx.compose.runtime.LaunchedEffect(resource) { if (!resource.isActive) resource.refresh() }
    val state by resource.state.collectAsState()
    return state
}

package br.com.talentflow.people.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
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

/** Selo em pílula, com fundo suave (mesma linguagem do site). */
@Composable
fun Tag(text: String, tone: Tone = Tone.Neutral) {
    val tf = LocalTf.current
    val (fg, bg) = when (tone) {
        Tone.Neutral -> tf.inkMuted to tf.sunken
        Tone.Positive -> tf.positive to tf.positiveSoft
        Tone.Attention -> tf.attention to tf.attentionSoft
        Tone.Critical -> tf.critical to tf.criticalSoft
        Tone.Info -> tf.info to tf.infoSoft
    }
    Surface(color = bg, contentColor = fg, shape = CircleShape) {
        Text(text, style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 10.dp, vertical = 2.dp))
    }
}

/** Cabeçalho de tela: rótulo em violeta, título em Fraunces e linha de apoio. */
@Composable
fun ScreenHeader(eyebrow: String, title: String, lead: String? = null, trailing: @Composable (() -> Unit)? = null) {
    Column(Modifier.fillMaxWidth().padding(bottom = 14.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.SpaceBetween) {
            Column(Modifier.weight(1f)) {
                Text(eyebrow.uppercase(), style = MaterialTheme.typography.labelSmall, color = LocalTf.current.brand)
                Spacer(Modifier.height(6.dp))
                Text(title, style = MaterialTheme.typography.headlineMedium)
            }
            trailing?.invoke()
        }
        if (lead != null) { Spacer(Modifier.height(6.dp)); Text(lead, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
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
    Surface(color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(18.dp), shadowElevation = 2.dp, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
        Column { content() }
    }
}

@Composable
fun Eyebrow(text: String, modifier: Modifier = Modifier) =
    Text(text.uppercase(), style = MaterialTheme.typography.labelSmall, color = LocalTf.current.brand, modifier = modifier.padding(top = 22.dp, bottom = 10.dp))

@Composable
fun Banner(text: String, tone: Tone = Tone.Attention) {
    val tf = LocalTf.current
    val (fg, bg) = when (tone) {
        Tone.Critical -> tf.critical to tf.criticalSoft
        Tone.Info -> tf.info to tf.infoSoft
        else -> tf.attention to tf.attentionSoft
    }
    Surface(color = bg, shape = RoundedCornerShape(14.dp), border = BorderStroke(1.dp, fg.copy(alpha = 0.5f)), modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
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
    Surface(border = BorderStroke(1.5.dp, MaterialTheme.colorScheme.outline), shape = RoundedCornerShape(18.dp), color = Color.Transparent, modifier = Modifier.fillMaxWidth()) {
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

private val Ease = CubicBezierEasing(0.2f, 0.8f, 0.2f, 1f)

/** Extremo do gradiente de ação (token gradAction): branco sobre #6C58F0 = 4,89:1. */
private val ActionEnd = Color(0xFF6C58F0)

/** Entrada suave (sobe e aparece), em cascata pelo atraso. Respeita a escala de animação do sistema. */
@Composable
fun Modifier.riseIn(delayMs: Int = 0): Modifier {
    val progress = remember { Animatable(0f) }
    LaunchedEffect(Unit) { progress.animateTo(1f, tween(durationMillis = 520, delayMillis = delayMs, easing = Ease)) }
    return this.graphicsLayer { alpha = progress.value; translationY = (1f - progress.value) * 36f }
}

/** Botão primário com gradiente de ação (texto branco com contraste AA nos dois extremos). */
@Composable
fun GradientButton(text: String, enabled: Boolean = true, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val tf = LocalTf.current
    val shape = RoundedCornerShape(16.dp)
    Box(
        modifier.heightIn(min = 52.dp).clip(shape)
            .background(Brush.linearGradient(listOf(tf.brand, ActionEnd)), alpha = if (enabled) 1f else 0.45f)
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { Text(text, color = tf.onBrand, style = MaterialTheme.typography.labelLarge, modifier = Modifier.padding(horizontal = 24.dp, vertical = 14.dp)) }
}

/** Iniciais sobre cor estável por nome (decorativo: o nome sempre aparece em texto ao lado). */
@Composable
fun Avatar(name: String, size: Int = 36) {
    val palette = listOf(0xFF5846D4, 0xFF0B6B63, 0xFF2A63A8, 0xFFB0364B, 0xFF8A5A12, 0xFF3D4A7A)
    val color = Color(palette[name.sumOf { it.code } % palette.size])
    val initials = name.trim().split(Regex("\\s+")).take(2).joinToString("") { it.take(1).uppercase() }.ifEmpty { "·" }
    Box(Modifier.size(size.dp).clip(CircleShape).background(Brush.linearGradient(listOf(color, color.copy(alpha = 0.7f)))), contentAlignment = Alignment.Center) {
        Text(initials, color = Color.White, style = MaterialTheme.typography.labelMedium)
    }
}

/** Cartão de indicador: faixa de cor de significado, número grande e nota. `value` já vem tratado ("—" sem dado). */
@Composable
fun KpiCard(label: String, value: String, note: String, tone: Tone = Tone.Neutral, delayMs: Int = 0, modifier: Modifier = Modifier) {
    val tf = LocalTf.current
    val accent = when (tone) { Tone.Positive -> tf.positive; Tone.Attention -> tf.attention; Tone.Info -> tf.info; Tone.Critical -> tf.critical; Tone.Neutral -> tf.brand }
    Surface(
        modifier = modifier.riseIn(delayMs), color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(20.dp),
        shadowElevation = 3.dp, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Row(Modifier.heightIn(min = 112.dp)) {
            Box(Modifier.width(4.dp).fillMaxHeight().background(accent))
            Column(Modifier.padding(start = 14.dp, end = 12.dp, top = 14.dp, bottom = 12.dp)) {
                Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(value, style = MaterialTheme.typography.displayMedium, color = MaterialTheme.colorScheme.onSurface)
                Text(note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

/** Painel branco arredondado com título, para gráficos e listas. */
@Composable
fun Panel(title: String, modifier: Modifier = Modifier, delayMs: Int = 0, content: @Composable () -> Unit) {
    Surface(
        modifier = modifier.fillMaxWidth().riseIn(delayMs), color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(22.dp),
        shadowElevation = 3.dp, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(14.dp))
            content()
        }
    }
}

/** Barra horizontal que cresce da esquerda ao aparecer. */
@Composable
fun GrowBar(fraction: Float, delayMs: Int = 0, modifier: Modifier = Modifier) {
    val tf = LocalTf.current
    val progress = remember { Animatable(0f) }
    LaunchedEffect(fraction) { progress.animateTo(fraction.coerceIn(0f, 1f), tween(durationMillis = 900, delayMillis = delayMs, easing = Ease)) }
    Box(modifier.height(12.dp).clip(CircleShape).background(MaterialTheme.colorScheme.surfaceVariant)) {
        Box(Modifier.fillMaxWidth(progress.value).fillMaxHeight().clip(CircleShape).background(Brush.horizontalGradient(listOf(tf.brand, tf.accent))))
    }
}

class DonutSlice(val label: String, val value: Int, val color: Color)

/** Rosca desenhada em Canvas; os arcos varrem ao aparecer. Sem dados: anel vazio e "—". */
@Composable
fun Donut(slices: List<DonutSlice>, centerLabel: String, modifier: Modifier = Modifier) {
    val total = slices.sumOf { it.value }
    val sweep = remember { Animatable(0f) }
    LaunchedEffect(total) { sweep.snapTo(0f); sweep.animateTo(1f, tween(durationMillis = 1100, easing = Ease)) }
    val track = MaterialTheme.colorScheme.surfaceVariant
    Box(modifier.size(132.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val stroke = 15.dp.toPx()
            val inset = stroke / 2
            val arcSize = Size(size.width - stroke, size.height - stroke)
            drawArc(track, 0f, 360f, false, Offset(inset, inset), arcSize, style = Stroke(stroke))
            if (total > 0) {
                var start = -90f
                slices.filter { it.value > 0 }.forEach { sl ->
                    val deg = 360f * sl.value / total
                    drawArc(sl.color, start, (deg - 3f).coerceAtLeast(0.5f) * sweep.value, false, Offset(inset, inset), arcSize, style = Stroke(stroke, cap = StrokeCap.Round))
                    start += deg
                }
            }
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(if (total == 0) "—" else total.toString(), style = MaterialTheme.typography.headlineSmall)
            Text(centerLabel, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

package br.com.talentflow.people.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import br.com.talentflow.core.User
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.ui.DonutSlice
import br.com.talentflow.people.ui.Donut
import br.com.talentflow.people.ui.Eyebrow
import br.com.talentflow.people.ui.GrowBar
import br.com.talentflow.people.ui.KpiCard
import br.com.talentflow.people.ui.Panel
import br.com.talentflow.people.ui.StateView
import br.com.talentflow.people.ui.Tone
import br.com.talentflow.people.ui.rememberLoad
import br.com.talentflow.people.ui.riseIn
import br.com.talentflow.people.ui.theme.LocalTf

private class Kpi(val label: String, val value: String, val note: String, val tone: Tone, val delayMs: Int)

/** Duas colunas de cartões; uma linha com um só cartão deixa o espaço vazio em vez de esticá-lo. */
@Composable
private fun KpiGrid(cards: List<Kpi>) {
    cards.chunked(2).forEach { pair ->
        Row(Modifier.fillMaxWidth().padding(bottom = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            pair.forEach { k -> KpiCard(k.label, k.value, k.note, k.tone, k.delayMs, Modifier.weight(1f)) }
            if (pair.size == 1) Box(Modifier.weight(1f))
        }
    }
}

@Composable
fun OverviewScreen(vm: AppViewModel, user: User) {
    val tf = LocalTf.current
    val dash = rememberLoad(vm.dashboard)
    val showPeople = user.role != "interviewer"
    val insights = if (showPeople) rememberLoad(vm.insights) else null
    Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp)) {
        // Faixa de boas-vindas em gradiente (decoração: o texto é branco sobre navy, contraste alto).
        Box(
            Modifier.fillMaxWidth().riseIn().clip(RoundedCornerShape(28.dp))
                .background(Brush.linearGradient(listOf(Color(0xFF0B1230), Color(0xFF2B2F7A), Color(0xFF5846D4)))).padding(22.dp),
        ) {
            Column {
                Text("VISÃO GERAL", style = MaterialTheme.typography.labelSmall, color = Color(0xFFCFC6FF))
                Spacer(Modifier.height(8.dp))
                Text("Olá, ${user.name.substringBefore(' ')}", style = MaterialTheme.typography.headlineMedium, color = Color.White)
                Spacer(Modifier.height(6.dp))
                Text("Situação atual calculada a partir dos registros do servidor.", style = MaterialTheme.typography.bodyMedium, color = Color(0xFFDCE1F7))
            }
        }
        StateView(dash, onRetry = { vm.dashboard.refresh() }) { d ->
            val m = d.metrics
            val total = m.candidatesActive + m.hired + m.rejected
            Eyebrow("Recrutamento")
            KpiGrid(listOf(
                Kpi("Vagas abertas", m.jobsOpen.toString(), "${m.jobsApproval} em aprovação", Tone.Neutral, 0),
                Kpi("Candidaturas ativas", m.candidatesActive.toString(), "${m.interviews} entrevista(s) agendada(s)", Tone.Info, 60),
                Kpi("Contratações", m.hired.toString(), "${m.rejected} reprovação(ões) registradas", Tone.Positive, 120),
                // Sem contratações não há média: mostramos "—", nunca um zero enganoso.
                Kpi("Tempo até contratar", if (m.hired == 0) "—" else "%.1f".format(m.avgTimeHire), if (m.hired == 0) "Sem contratações para calcular" else "dias, média das contratações", Tone.Attention, 180),
                Kpi("Conversão", if (total == 0) "—" else "%.1f%%".format(m.conversion), "contratados ÷ candidaturas totais", Tone.Neutral, 240),
            ))
            Spacer(Modifier.height(8.dp))
            Panel("Funil por etapa", delayMs = 120) {
                if (d.stages.isEmpty()) Text("Sem candidaturas ainda.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                val max = (d.stages.maxOfOrNull { it.value } ?: 1).coerceAtLeast(1)
                d.stages.forEachIndexed { n, s ->
                    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(s.name, style = MaterialTheme.typography.bodySmall, modifier = Modifier.width(108.dp))
                        GrowBar(s.value / max.toFloat(), delayMs = n * 70, modifier = Modifier.weight(1f))
                        Text(s.value.toString(), style = MaterialTheme.typography.labelMedium, textAlign = TextAlign.End, modifier = Modifier.width(36.dp))
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
            Panel("Situação das candidaturas", delayMs = 160) {
                val slices = listOf(
                    DonutSlice("Ativas", m.candidatesActive, tf.brand),
                    DonutSlice("Contratadas", m.hired, Color(0xFF12906A)),
                    DonutSlice("Reprovadas", m.rejected, Color(0xFFC0506A)),
                )
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                    Donut(slices, "candidaturas")
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        slices.forEach { sl ->
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(Modifier.size(12.dp).clip(RoundedCornerShape(4.dp)).background(sl.color))
                                Spacer(Modifier.width(10.dp))
                                Text(sl.label, style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                                Text(sl.value.toString(), style = MaterialTheme.typography.labelMedium)
                            }
                        }
                    }
                }
            }
        }
        if (insights != null) {
            Eyebrow("Pessoas")
            StateView(insights, onRetry = { vm.insights.refresh() }) { i ->
                KpiGrid(listOf(
                    Kpi("Colaboradores ativos", i.active.toString(), "de ${i.population} registrados", Tone.Neutral, 0),
                    Kpi("Ausências pendentes", i.pendingLeaves.toString(), "aguardando decisão", Tone.Attention, 60),
                ))
                KpiCard(
                    "Planos de desenvolvimento concluídos", if (i.planCount == 0) "—" else "${i.completedPlans}/${i.planCount}",
                    "Execução de PDI, não evidência de ganho de competência", Tone.Positive, 120, Modifier.fillMaxWidth(),
                )
            }
        }
        Spacer(Modifier.height(16.dp))
    }
}

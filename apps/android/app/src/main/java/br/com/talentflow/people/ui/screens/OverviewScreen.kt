package br.com.talentflow.people.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import br.com.talentflow.core.User
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.ui.Eyebrow
import br.com.talentflow.people.ui.Ledger
import br.com.talentflow.people.ui.LedgerRow
import br.com.talentflow.people.ui.Rule
import br.com.talentflow.people.ui.ScreenHeader
import br.com.talentflow.people.ui.StateView
import br.com.talentflow.people.ui.rememberLoad
import br.com.talentflow.people.ui.theme.LocalTf

@Composable
fun OverviewScreen(vm: AppViewModel, user: User) {
    val dash = rememberLoad(vm.dashboard)
    val showPeople = user.role != "interviewer"
    val insights = if (showPeople) rememberLoad(vm.insights) else null
    Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp)) {
        ScreenHeader("Visão geral", "Olá, ${user.name.substringBefore(' ')}", "Situação atual calculada a partir dos registros do servidor.")
        StateView(dash, onRetry = { vm.dashboard.refresh() }) { d ->
            val m = d.metrics
            Eyebrow("Recrutamento", Modifier.padding(top = 4.dp))
            Ledger {
                LedgerRow("Vagas abertas", "${m.jobsApproval} em aprovação", m.jobsOpen.toString()); Rule()
                LedgerRow("Candidaturas ativas", "${m.interviews} entrevista(s) agendada(s)", m.candidatesActive.toString()); Rule()
                LedgerRow("Contratações", "${m.rejected} reprovação(ões) registradas", m.hired.toString()); Rule()
                // Sem contratações não há média: mostramos "—", nunca um zero enganoso.
                LedgerRow("Tempo até contratar", if (m.hired == 0) "Sem contratações para calcular" else "dias, média das contratações", if (m.hired == 0) "—" else "%.1f".format(m.avgTimeHire)); Rule()
                val total = m.candidatesActive + m.hired + m.rejected
                LedgerRow("Conversão", "contratados ÷ candidaturas totais", if (total == 0) "—" else "%.1f%%".format(m.conversion))
            }
            Eyebrow("Funil por etapa")
            if (d.stages.isEmpty()) Text("Sem candidaturas ainda.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            val max = (d.stages.maxOfOrNull { it.value } ?: 1).coerceAtLeast(1)
            d.stages.forEach { s ->
                Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(s.name, style = MaterialTheme.typography.bodySmall, modifier = Modifier.width(112.dp))
                    Box(Modifier.weight(1f).height(10.dp).clip(RoundedCornerShape(2.dp)).background(MaterialTheme.colorScheme.surfaceVariant)) {
                        Box(Modifier.fillMaxWidth(s.value / max.toFloat()).height(10.dp).background(LocalTf.brand))
                    }
                    Text(s.value.toString(), style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.End, modifier = Modifier.width(36.dp))
                }
            }
        }
        if (insights != null) {
            Eyebrow("Pessoas")
            StateView(insights, onRetry = { vm.insights.refresh() }) { i ->
                Ledger {
                    LedgerRow("Colaboradores ativos", "de ${i.population} registrados", i.active.toString()); Rule()
                    LedgerRow("Planos de desenvolvimento concluídos", "Execução de PDI, não evidência de ganho de competência", if (i.planCount == 0) "—" else "${i.completedPlans}/${i.planCount}"); Rule()
                    LedgerRow("Ausências pendentes", "aguardando decisão", i.pendingLeaves.toString())
                }
            }
        }
    }
}

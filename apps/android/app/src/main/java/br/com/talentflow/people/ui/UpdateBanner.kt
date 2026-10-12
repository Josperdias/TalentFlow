package br.com.talentflow.people.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import br.com.talentflow.people.BuildConfig
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.data.UpdateState
import br.com.talentflow.people.ui.theme.LocalTf

/** Faixa de atualização dentro do app: nova build publicada -> "Atualizar agora" -> baixa, confere e o Android confirma. Sem navegador. */
@Composable
fun UpdateBanner(vm: AppViewModel) {
    val state by vm.update.collectAsState()
    val tf = LocalTf.current
    if (state is UpdateState.Idle) return
    Surface(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp).padding(bottom = 12.dp).riseIn(),
        color = tf.brandSoft, shape = RoundedCornerShape(20.dp), border = BorderStroke(1.dp, tf.brand.copy(alpha = 0.4f)),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            when (val s = state) {
                is UpdateState.Available -> {
                    Text("Nova versão ${s.info.version} disponível", style = MaterialTheme.typography.titleMedium)
                    Text(
                        s.info.notes.ifBlank { "Você usa a ${BuildConfig.VERSION_NAME}. A atualização baixa dentro do app e o Android pede sua confirmação." },
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 4,
                    )
                    GradientButton("Atualizar agora", modifier = Modifier.fillMaxWidth()) { vm.startUpdate() }
                }
                is UpdateState.NeedsPermission -> {
                    Text("Permita instalar atualizações", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "O Android pede uma permissão única: ative \"Permitir desta fonte\" para o TalentFlow, volte e toque em Continuar.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    GradientButton("Continuar", modifier = Modifier.fillMaxWidth()) { vm.startUpdate() }
                }
                is UpdateState.Downloading -> {
                    Text("Baixando a versão ${s.info.version}…", style = MaterialTheme.typography.titleMedium)
                    val frac = if (s.info.size > 0) (s.done.toFloat() / s.info.size).coerceIn(0f, 1f) else 0f
                    LinearProgressIndicator(progress = { frac }, modifier = Modifier.fillMaxWidth().height(8.dp))
                }
                is UpdateState.WaitingConfirm -> {
                    Text("Confirme a atualização na tela do Android", style = MaterialTheme.typography.titleMedium)
                    Text("O app fecha ao atualizar; abra-o de novo em seguida.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                is UpdateState.Failed -> {
                    Text("Não foi possível atualizar", style = MaterialTheme.typography.titleMedium)
                    Text(s.message, style = MaterialTheme.typography.bodySmall, color = tf.critical)
                    if (s.info != null) GradientButton("Tentar de novo", modifier = Modifier.fillMaxWidth()) { vm.startUpdate() }
                }
                UpdateState.Idle -> Spacer(Modifier.height(0.dp))
            }
        }
    }
}

package br.com.talentflow.people.data

import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.net.Uri
import android.provider.Settings
import androidx.core.content.IntentCompat
import kotlinx.coroutines.flow.MutableStateFlow
import java.io.File

/**
 * Instala a atualização já baixada e verificada, SEM abrir o navegador, pela API PackageInstaller do Android.
 * O sistema mostra a confirmação "Atualizar este aplicativo?" (obrigatória fora de apps de sistema); o resultado volta por
 * [InstallResultReceiver]. O Android só aceita a atualização se o APK tiver a MESMA assinatura do instalado.
 */
object UpdateInstaller {
    const val ACTION = "br.com.talentflow.people.INSTALL_RESULT"

    /** Mensagem de falha vinda do instalador do sistema (null = sem falha). */
    val failure = MutableStateFlow<String?>(null)

    fun canInstall(ctx: Context): Boolean = ctx.packageManager.canRequestPackageInstalls()

    /** Abre a tela do Android onde a pessoa permite "instalar apps desta fonte" para o TalentFlow. */
    fun openPermissionSettings(ctx: Context) {
        ctx.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:${ctx.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    fun install(ctx: Context, apk: File) {
        failure.value = null
        val installer = ctx.packageManager.packageInstaller
        val params = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL).apply { setAppPackageName(ctx.packageName) }
        val id = installer.createSession(params)
        installer.openSession(id).use { session ->
            apk.inputStream().use { input ->
                session.openWrite("talentflow-update.apk", 0, apk.length()).use { out -> input.copyTo(out); session.fsync(out) }
            }
            val intent = Intent(ctx, InstallResultReceiver::class.java).setAction(ACTION).setPackage(ctx.packageName)
            val pending = PendingIntent.getBroadcast(ctx, id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE)
            session.commit(pending.intentSender)
        }
    }
}

class InstallResultReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                // O sistema pede a confirmação da pessoa: abrimos a tela dele.
                val confirm = IntentCompat.getParcelableExtra(intent, Intent.EXTRA_INTENT, Intent::class.java)
                if (confirm != null) context.startActivity(confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
            PackageInstaller.STATUS_SUCCESS -> UpdateInstaller.failure.value = null // o app é substituído e reiniciado pelo sistema
            else -> UpdateInstaller.failure.value = when (status) {
                PackageInstaller.STATUS_FAILURE_CONFLICT, PackageInstaller.STATUS_FAILURE_INCOMPATIBLE ->
                    "O Android recusou: a assinatura desta versão é diferente da instalada. Isso acontece com builds de depuração " +
                        "(cada build usa uma chave) — instale uma build assinada com a chave de release uma vez; depois as atualizações funcionam."
                PackageInstaller.STATUS_FAILURE_ABORTED -> "A atualização foi cancelada."
                PackageInstaller.STATUS_FAILURE_STORAGE -> "Sem espaço suficiente para atualizar."
                else -> intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)?.let { "O Android não conseguiu instalar: $it" } ?: "O Android não conseguiu instalar a atualização."
            }
        }
    }
}

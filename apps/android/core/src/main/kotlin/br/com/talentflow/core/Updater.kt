package br.com.talentflow.core

import java.io.File
import java.security.DigestOutputStream
import java.security.MessageDigest

/** O arquivo baixado não confere com o SHA-256 anunciado pelo servidor: nunca é instalado. */
class UpdateIntegrityException(message: String) : Exception(message)

/**
 * Atualização do aplicativo: consulta o PRÓPRIO servidor (que lê pasta própria ou Releases do GitHub), baixa para uma pasta
 * temporária, confere o SHA-256 (obrigatório) e devolve o arquivo. Quem chama entrega ao instalador do sistema.
 */
object Updater {
    /** Devolve a atualização somente se for MAIS NOVA que a versão em execução. */
    suspend fun check(api: ApiClient, currentVersion: String, platform: String = "android"): UpdateInfo? {
        val info = api.updateInfo(platform)
        return if (info.available && info.sha256.length == 64 && isVersionNewer(currentVersion, info.version)) info else null
    }

    suspend fun downloadAndVerify(api: ApiClient, info: UpdateInfo, folder: File, fileName: String, onProgress: (Long) -> Unit = {}): File {
        if (info.sha256.length != 64 || !info.sha256.all { it.isDigit() || it.lowercaseChar() in 'a'..'f' })
            throw UpdateIntegrityException("O servidor não informou um SHA-256 válido para a atualização.")
        folder.mkdirs()
        val target = File(folder, fileName); val partial = File(folder, "$fileName.part")
        val digest = MessageDigest.getInstance("SHA-256")
        try {
            partial.outputStream().use { out -> DigestOutputStream(out, digest).use { api.download(info.url, it, onProgress) } }
            val hash = digest.digest().joinToString("") { "%02x".format(it) }
            if (!hash.equals(info.sha256, ignoreCase = true))
                throw UpdateIntegrityException("O arquivo baixado não confere com o SHA-256 anunciado. A atualização foi cancelada.")
        } catch (e: Throwable) { partial.delete(); throw e }
        target.delete()
        if (!partial.renameTo(target)) { partial.delete(); throw UpdateIntegrityException("Não foi possível gravar o arquivo de atualização.") }
        return target
    }
}

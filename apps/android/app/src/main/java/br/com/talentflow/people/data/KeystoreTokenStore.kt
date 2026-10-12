package br.com.talentflow.people.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import br.com.talentflow.core.TokenStore
import br.com.talentflow.core.Tokens
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Guarda access/refresh token cifrados (AES-256-GCM) com chave não exportável do Android Keystore.
 * Se a chave for invalidada (ex.: restauração do aparelho) ou o dado corrompido, descarta e exige novo login.
 */
class KeystoreTokenStore(context: Context) : TokenStore {
    private val prefs = context.getSharedPreferences("tf_secure", Context.MODE_PRIVATE)

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        gen.init(
            KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()
        )
        return gen.generateKey()
    }

    @Synchronized
    override fun save(tokens: Tokens?) {
        if (tokens == null) { prefs.edit().remove(PREF).apply(); return }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val sealed = cipher.doFinal("${tokens.access}\n${tokens.refresh}".toByteArray(Charsets.UTF_8))
        val packed = Base64.encodeToString(cipher.iv + sealed, Base64.NO_WRAP)
        prefs.edit().putString(PREF, packed).apply()
    }

    @Synchronized
    override fun load(): Tokens? {
        val packed = prefs.getString(PREF, null) ?: return null
        return try {
            val bytes = Base64.decode(packed, Base64.NO_WRAP)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes, 0, IV_BYTES))
            val parts = String(cipher.doFinal(bytes, IV_BYTES, bytes.size - IV_BYTES), Charsets.UTF_8).split('\n')
            if (parts.size == 2) Tokens(parts[0], parts[1]) else null
        } catch (_: Exception) {
            prefs.edit().remove(PREF).apply(); null
        }
    }

    private companion object {
        const val ALIAS = "talentflow_tokens_v1"
        const val PREF = "tokens"
        const val IV_BYTES = 12
    }
}

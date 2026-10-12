package br.com.talentflow.people

import android.graphics.Bitmap
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.onRoot
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/**
 * Teste da INTERFACE do app real em emulador: servidor -> login -> visão geral -> vagas -> criar vaga pela UI
 * e, em seguida, uma vaga criada por OUTRO cliente (chamada direta à API) deve aparecer na tela sem recarregar.
 * Usa a API real (FastAPI + PostgreSQL) do runner; o emulador a enxerga em http://10.0.2.2:8000 (só builds debug).
 */
@RunWith(AndroidJUnit4::class)
@OptIn(ExperimentalTestApi::class)
class LoginAndSyncTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

    private val args = InstrumentationRegistry.getArguments()
    private val server = args.getString("tfServer", "http://10.0.2.2:8000")
    private val password = "Demo@2026!"

    private fun shot(name: String) {
        val dir = File(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null), "screenshots").apply { mkdirs() }
        File(dir, "$name.png").outputStream().use { rule.onRoot().captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, it) }
    }

    private fun waitForText(text: String, ms: Long = 20_000) =
        rule.waitUntil(ms) { rule.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty() }

    /** "Outro cliente": fala direto com a API como o app do Windows ou o site fariam. */
    private fun apiToken(email: String): String {
        val c = URL("$server/api/v1/auth/token").openConnection() as HttpURLConnection
        c.requestMethod = "POST"; c.doOutput = true; c.setRequestProperty("Content-Type", "application/json")
        c.outputStream.use { it.write("""{"email":"$email","password":"$password","client":"windows","device":"outro-cliente"}""".toByteArray()) }
        return JSONObject(c.inputStream.bufferedReader().readText()).getString("access_token")
    }

    private fun apiCreateJob(token: String, title: String) {
        val c = URL("$server/api/v1/jobs").openConnection() as HttpURLConnection
        c.requestMethod = "POST"; c.doOutput = true
        c.setRequestProperty("Content-Type", "application/json"); c.setRequestProperty("Authorization", "Bearer $token")
        c.outputStream.use { it.write("""{"title":"$title","status":"open"}""".toByteArray()) }
        assertTrue("API deve aceitar a criação (HTTP ${c.responseCode})", c.responseCode == 200)
    }

    private fun apiJobTitles(token: String): List<String> {
        val c = URL("$server/api/v1/jobs").openConnection() as HttpURLConnection
        c.setRequestProperty("Authorization", "Bearer $token")
        val arr = org.json.JSONArray(c.inputStream.bufferedReader().readText())
        return (0 until arr.length()).map { arr.getJSONObject(it).getString("title") }
    }

    @Test
    fun login_pela_interface_criar_vaga_e_sincronizar_com_outro_cliente() {
        // 1) Primeiro uso: endereço do servidor (nenhum domínio é presumido)
        waitForText("Conectar ao servidor")
        shot("android-01-servidor")
        rule.onNodeWithText("Endereço do servidor").performTextInput(server)
        rule.onNode(hasText("Continuar") and hasClickAction()).performClick()

        // 2) Login com formulário nativo
        waitForText("Entrar")
        rule.onNodeWithText("E-mail").performTextInput("admin@nexa.demo")
        rule.onNodeWithText("Senha").performTextInput(password)
        shot("android-02-login")
        rule.onNode(hasText("Entrar") and hasClickAction()).performClick()

        // 3) Visão geral com dados reais do PostgreSQL
        waitForText("Olá, Marina")
        waitForText("Vagas abertas")
        shot("android-03-visao-geral")

        // 4) Vagas: lista real
        rule.onNode(hasText("Vagas") and hasClickAction()).performClick()
        waitForText("Nova vaga")
        shot("android-04-vagas")

        // 5) Criar vaga pela interface -> existe no servidor
        val ui = "Vaga criada no app Android ${System.currentTimeMillis()}"
        rule.onNode(hasText("Nova vaga") and hasClickAction()).performClick()
        rule.onNodeWithText("Título da vaga").performTextInput(ui)
        rule.onNode(hasText("Criar vaga") and hasClickAction()).performClick()
        waitForText(ui)
        val token = apiToken("admin@nexa.demo")
        assertTrue("A vaga criada no app deve existir no servidor", apiJobTitles(token).contains(ui))

        // 6) OUTRO cliente cria uma vaga -> aparece no app SEM recarregar (feed de sincronização)
        val other = "Vaga criada por outro cliente ${System.currentTimeMillis()}"
        apiCreateJob(token, other)
        waitForText(other, 30_000)
        shot("android-05-sincronizado")
    }
}

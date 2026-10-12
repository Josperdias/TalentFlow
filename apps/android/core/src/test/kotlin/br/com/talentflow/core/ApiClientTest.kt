package br.com.talentflow.core

import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test

class ApiClientTest {
    private lateinit var server: MockWebServer
    private lateinit var store: MemoryTokenStore
    private lateinit var api: ApiClient

    private val userJson = """{"id":1,"name":"Marina","email":"m@x","role":"admin","company_id":1,"company":"Nexa"}"""
    private fun tokenBody(a: String, r: String) = """{"token_type":"Bearer","access_token":"$a","refresh_token":"$r","expires_in":900,"user":$userJson}"""

    @Before fun setUp() {
        server = MockWebServer().also { it.start() }
        store = MemoryTokenStore()
        api = ApiClient(server.url("/api/v1").toString().trimEnd('/'), store, "android", "Teste")
    }
    @After fun tearDown() { server.shutdown() }

    private fun json(code: Int, body: String) = MockResponse().setResponseCode(code).setHeader("Content-Type", "application/json").setBody(body)

    @Test fun `login guarda tokens e envia client e device`() = runBlocking {
        server.enqueue(json(200, tokenBody("A1", "R1")))
        val user = api.login(" m@x ", "senha")
        assertEquals("Marina", user.name)
        assertEquals(Tokens("A1", "R1"), store.load())
        val sent = server.takeRequest()
        assertEquals("/api/v1/auth/token", sent.path)
        assertTrue(sent.body.readUtf8().contains("\"client\":\"android\""))
        assertNull("login não deve enviar Authorization", sent.getHeader("Authorization"))
    }

    @Test fun `senha errada vira ApiException com mensagem do servidor e nao guarda tokens`() = runBlocking {
        server.enqueue(json(401, """{"detail":"Credenciais inválidas"}"""))
        try { api.login("a@b", "x"); fail() } catch (e: ApiException) {
            assertEquals(401, e.status); assertEquals("Credenciais inválidas", e.message)
        }
        assertNull(store.load())
    }

    @Test fun `401 faz refresh uma vez e repete a chamada com o novo token`() = runBlocking {
        store.save(Tokens("velho", "R1"))
        server.enqueue(json(401, """{"detail":"Sessão expirada"}"""))
        server.enqueue(json(200, """{"access_token":"novo","refresh_token":"R2"}"""))
        server.enqueue(json(200, """[]"""))
        assertEquals(0, api.jobs().size)
        assertEquals("Bearer velho", server.takeRequest().getHeader("Authorization"))
        val refresh = server.takeRequest()
        assertEquals("/api/v1/auth/refresh", refresh.path)
        assertTrue(refresh.body.readUtf8().contains("R1"))
        assertEquals("Bearer novo", server.takeRequest().getHeader("Authorization"))
        assertEquals(Tokens("novo", "R2"), store.load())
    }

    @Test fun `refresh recusado apaga tokens e exige novo login`() = runBlocking {
        store.save(Tokens("velho", "R1"))
        server.enqueue(json(401, """{"detail":"Sessão expirada"}"""))
        server.enqueue(json(401, """{"detail":"Refresh token reutilizado"}"""))
        try { api.jobs(); fail() } catch (_: AuthExpiredException) { }
        assertNull(store.load())
    }

    @Test fun `PATCH envia If-Match e 409 expoe a versao atual`() = runBlocking {
        store.save(Tokens("A", "R"))
        server.enqueue(json(409, """{"detail":{"message":"O registro foi alterado por outra sessão.","current_version":7,"current":{"title":"x"}}}"""))
        val job = Job(id = 5, code = "TF-00005", title = "Antiga", version = 3)
        try { api.updateJobTitle(job, "Nova"); fail() } catch (e: ApiException) {
            assertTrue(e.isConflict); assertEquals(7, e.currentVersion); assertEquals("O registro foi alterado por outra sessão.", e.message)
        }
        val req = server.takeRequest()
        assertEquals("PATCH", req.method); assertEquals("3", req.getHeader("If-Match"))
    }

    @Test fun `mover candidatura envia a versao da candidatura`() = runBlocking {
        store.save(Tokens("A", "R"))
        server.enqueue(json(200, """{"ok":true,"stage":"Triagem","status":"active","version":4}"""))
        val app = ApplicationRow(id = 9, candidateId = 1, jobId = 2, stageId = 10, version = 3, candidate = Candidate(1, "Ana"))
        val r = api.moveApplication(app, 11)
        assertEquals(4, r.version)
        val req = server.takeRequest()
        assertEquals("/api/v1/applications/9/move", req.path); assertEquals("3", req.getHeader("If-Match"))
    }

    @Test fun `falha de rede vira NetworkException`() = runBlocking {
        store.save(Tokens("A", "R")); server.shutdown()
        try { api.jobs(); fail() } catch (_: NetworkException) { }
    }

    @Test fun `erro de validacao em lista vira mensagem generica`() = runBlocking {
        store.save(Tokens("A", "R"))
        server.enqueue(json(422, """{"detail":[{"loc":["body","title"],"msg":"too short"}]}"""))
        try { api.createJob("a", "", "", "open"); fail() } catch (e: ApiException) { assertEquals("Revise os campos informados.", e.message) }
    }

    @Test fun `logout limpa tokens mesmo sem rede`() = runBlocking {
        store.save(Tokens("A", "R")); server.shutdown()
        api.logout()
        assertNull(store.load())
    }

    @Test fun `feed de mudancas busca o cursor e depois so o que mudou`() = runBlocking {
        store.save(Tokens("A", "R"))
        server.enqueue(json(200, """{"cursor":10}"""))
        server.enqueue(json(200, """{"cursor":12,"latest":12,"has_more":false,"entities":["job","application"],"items":[{"seq":11,"entity":"job","action":"updated"},{"seq":12,"entity":"application","action":"stage_changed"}]}"""))
        val feed = ChangeFeed(api)
        assertEquals(setOf("job", "application"), feed.poll())
        assertEquals("/api/v1/changes/cursor", server.takeRequest().path)
        assertEquals("/api/v1/changes?after=10&limit=200", server.takeRequest().path)
        server.enqueue(json(200, """{"cursor":12,"latest":12,"has_more":false,"entities":[],"items":[]}"""))
        assertTrue(feed.poll().isEmpty())
        assertEquals("/api/v1/changes?after=12&limit=200", server.takeRequest().path)
    }
}

class ServerUrlTest {
    @Test fun `normaliza enderecos validos`() {
        assertEquals("https://rh.empresa.com.br/api/v1", ServerUrl.toApiBase("rh.empresa.com.br"))
        assertEquals("https://rh.empresa.com.br/api/v1", ServerUrl.toApiBase(" https://rh.empresa.com.br/ "))
        assertEquals("https://rh.empresa.com.br/api/v1", ServerUrl.toApiBase("https://rh.empresa.com.br/api/v1/"))
        assertEquals("https://x.com/talentflow/api/v1", ServerUrl.toApiBase("https://x.com/talentflow"))
    }
    @Test fun `recusa http sem permissao e entradas invalidas`() {
        assertNull(ServerUrl.toApiBase("http://rh.empresa.com.br"))
        assertEquals("http://10.0.2.2:8000/api/v1", ServerUrl.toApiBase("http://10.0.2.2:8000", allowInsecure = true))
        assertNull(ServerUrl.toApiBase(""))
        assertNull(ServerUrl.toApiBase("https://user:pw@x.com"))
        assertNull(ServerUrl.toApiBase("https://x.com/?a=1"))
    }
}

class VersionTest {
    @Test fun `compara versoes ignorando sufixo rc`() {
        assertTrue(isVersionBelow("1.2.9", "1.3.0")); assertFalse(isVersionBelow("1.3.0-rc.1", "1.3.0"))
        assertFalse(isVersionBelow("2.0.0", "1.9.9")); assertTrue(isVersionBelow("1.0", "1.0.1"))
        assertNotNull(Dashboard(DashboardMetrics()))
    }
}

package br.com.talentflow.core

import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okio.Buffer
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest

class UpdaterTest {
    private lateinit var server: MockWebServer
    private lateinit var store: MemoryTokenStore
    private lateinit var api: ApiClient
    private fun sha(b: ByteArray) = MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }
    private fun tmp(): File = Files.createTempDirectory("tf-upd").toFile()
    private fun bytes(b: ByteArray) = MockResponse().setBody(Buffer().write(b))

    @Before fun setUp() {
        server = MockWebServer().also { it.start() }
        store = MemoryTokenStore().also { it.save(Tokens("acc", "ref")) }
        api = ApiClient(server.url("/rh/api/v1").toString().trimEnd('/'), store, "android", "Teste")
    }
    @After fun tearDown() { server.shutdown() }

    @Test fun `precedencia semantica`() {
        assertTrue(isVersionNewer("1.3.0-rc.1", "1.3.0-rc.2"))
        assertTrue(isVersionNewer("1.3.0-rc.2", "1.3.0-rc.10"))
        assertTrue(isVersionNewer("1.3.0-rc.9", "1.3.0"))
        assertFalse(isVersionNewer("1.3.0", "1.3.0-rc.9"))
        assertFalse(isVersionNewer("1.3.0", "1.3.0"))
        assertTrue(isVersionNewer("1.3.9", "1.4.0"))
        assertFalse(isVersionNewer("2.0.0", "1.99.99"))
        assertFalse(isVersionNewer("1.3.0+b5", "1.3.0"))
    }

    @Test fun `baixa confere sha256 e resolve caminho em subpasta com token`() = runBlocking {
        val blob = ByteArray(200_000) { (it % 251).toByte() }
        server.enqueue(bytes(blob))
        val info = UpdateInfo(true, "1.4.0", "/api/v1/client-updates/android/download/a.apk", sha(blob), blob.size.toLong())
        val f = Updater.downloadAndVerify(api, info, tmp(), "update.apk")
        assertArrayEquals(blob, f.readBytes())
        val req = server.takeRequest()
        assertEquals("/rh/api/v1/client-updates/android/download/a.apk", req.path)
        assertEquals("Bearer acc", req.getHeader("Authorization"))
    }

    @Test fun `sha256 diferente cancela e nao deixa arquivo`() = runBlocking {
        server.enqueue(bytes("adulterado".toByteArray()))
        val dir = tmp()
        try { Updater.downloadAndVerify(api, UpdateInfo(true, "1.4.0", "/api/v1/x.apk", "a".repeat(64), 10), dir, "u.apk"); fail() }
        catch (e: UpdateIntegrityException) { /* esperado */ }
        assertEquals(0, dir.listFiles()!!.size)
    }

    @Test fun `sem sha256 valido nem baixa`() = runBlocking {
        try { Updater.downloadAndVerify(api, UpdateInfo(true, "1.4.0", "/api/v1/x.apk", "", 1), tmp(), "u.apk"); fail() }
        catch (e: UpdateIntegrityException) { /* esperado */ }
        assertEquals(0, server.requestCount)
    }

    @Test fun `outro host exige https`() = runBlocking {
        try { Updater.downloadAndVerify(api, UpdateInfo(true, "1.4.0", "http://cdn.exemplo.test/a.apk", "b".repeat(64), 1), tmp(), "u.apk"); fail() }
        catch (e: ApiException) { assertEquals(400, e.status) }
        assertEquals(0, server.requestCount)
    }

    @Test fun `check so oferece versao mais nova`() = runBlocking {
        val body = """{"available":true,"version":"1.3.0","url":"/api/v1/client-updates/android/download/a.apk","sha256":"${"c".repeat(64)}","size":1}"""
        fun json(b: String) = MockResponse().setHeader("Content-Type", "application/json").setBody(b)
        server.enqueue(json(body)); assertNull(Updater.check(api, "1.3.0"))
        server.enqueue(json(body)); assertEquals("1.3.0", Updater.check(api, "1.3.0-rc.1")?.version)
        server.enqueue(json("""{"available":false,"reason":"nada"}""")); assertNull(Updater.check(api, "1.0.0"))
    }
}

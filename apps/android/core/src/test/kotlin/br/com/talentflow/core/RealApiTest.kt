package br.com.talentflow.core

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Assume.assumeTrue
import org.junit.Test

/**
 * Integração contra a API REAL (FastAPI + PostgreSQL). Só roda com TF_API_URL, ex.:
 *   TF_API_URL=http://127.0.0.1:8000 ./gradlew -PcoreOnly=true :core:test --tests '*RealApiTest*'
 * Usa dois "dispositivos" (dois clientes) para provar sincronização e conflito entre eles.
 */
class RealApiTest {
    private val base = System.getenv("TF_API_URL")?.let { ServerUrl.toApiBase(it, allowInsecure = true) }
    private val password = "Demo@2026!"

    private fun client(device: String) = ApiClient(base!!, MemoryTokenStore(), "android", device)

    @Test fun `login real, leitura autorizada e isolamento entre empresas`() = runBlocking {
        assumeTrue("TF_API_URL não definido", base != null)
        val nexa = client("A"); val orbe = client("B")
        assertEquals("admin", nexa.login("admin@nexa.demo", password).role)
        orbe.login("admin@orbe.demo", password)
        val nexaJobs = nexa.jobs(); val orbeJobs = orbe.jobs()
        assertTrue(nexaJobs.isNotEmpty())
        assertTrue("empresas não podem compartilhar vagas", nexaJobs.map { it.id }.intersect(orbeJobs.map { it.id }.toSet()).isEmpty())
        try { orbe.jobDetail(nexaJobs.first().id); fail("Orbe leu vaga da Nexa") } catch (e: ApiException) { assertEquals(404, e.status) }
        assertTrue(nexa.health().apiVersion.isNotBlank())
        val trend = nexa.trend()
        assertTrue("evolução mensal real", trend.points.isNotEmpty() && trend.totalApplications == trend.points.sumOf { it.applications })
    }

    @Test fun `criar no aparelho A aparece no aparelho B e conflito e detectado`() = runBlocking {
        assumeTrue("TF_API_URL não definido", base != null)
        val a = client("A"); val b = client("B")
        a.login("admin@nexa.demo", password); b.login("recrutador@nexa.demo", password)
        val feedB = ChangeFeed(b); feedB.poll() // posiciona o cursor
        val created = a.createJob("Vaga criada no Android ${System.nanoTime()}", "Tecnologia", "Remoto", "open")
        assertTrue("feed do B deve avisar mudança em 'job'", "job" in feedB.poll())
        assertTrue(b.jobs().any { it.id == created.id })
        // B edita primeiro; A tenta salvar com a versão antiga -> 409
        val seenByB = b.jobDetail(created.id).job
        b.updateJobTitle(seenByB, "Editada no B ${System.nanoTime()}")
        try { a.updateJobTitle(created, "Edição do A que não pode vencer"); fail("deveria dar conflito") }
        catch (e: ApiException) { assertTrue(e.isConflict); assertTrue(e.currentVersion!! > created.version) }
        assertTrue(a.jobDetail(created.id).job.title.startsWith("Editada no B"))
    }

    @Test fun `refresh real rotaciona e sessao revogada exige novo login`() = runBlocking {
        assumeTrue("TF_API_URL não definido", base != null)
        val store = MemoryTokenStore(); val c = ApiClient(base!!, store, "windows", "PC")
        c.login("gestor@nexa.demo", password)
        val before = store.load()!!
        store.save(before.copy(access = "token-invalido")) // força 401 -> refresh real
        assertTrue(c.dashboard().metrics.jobsOpen >= 0)
        assertTrue("refresh deve ter rotacionado o token", store.load()!!.refresh != before.refresh)
        c.logout()
        assertEquals(null, store.load())
    }
}

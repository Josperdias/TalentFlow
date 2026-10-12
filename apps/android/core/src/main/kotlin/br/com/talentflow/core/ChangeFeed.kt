package br.com.talentflow.core

/**
 * Acompanha /changes. O feed é só uma dica de invalidação: quando algo mudou, a UI rebusca
 * a lista pelo endpoint normal (que aplica RBAC). Mantém o cursor entre chamadas.
 */
class ChangeFeed(private val api: ApiClient) {
    private var cursor: Long? = null

    /** Entidades alteradas desde a última chamada (vazio se nada mudou). Lança em falha de rede/sessão. */
    suspend fun poll(): Set<String> {
        val start = cursor ?: api.get("/changes/cursor", Cursor.serializer()).cursor.also { cursor = it }
        val changed = linkedSetOf<String>()
        var after = start
        do {
            val page = api.get("/changes?after=$after&limit=200", Changes.serializer())
            changed += page.entities
            after = page.cursor
            cursor = after
        } while (page.hasMore)
        return changed
    }

    fun reset() { cursor = null }
}

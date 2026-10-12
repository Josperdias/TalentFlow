package br.com.talentflow.people.data

import br.com.talentflow.core.ApiException
import br.com.talentflow.core.AuthExpiredException
import br.com.talentflow.core.NetworkException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface Load<out T> {
    data object Idle : Load<Nothing>
    data object Loading : Load<Nothing>
    /** [stale] = a última atualização falhou (sem conexão): mostramos o que já tínhamos, com aviso. */
    data class Ready<T>(val data: T, val stale: Boolean = false) : Load<T>
    data class Failed(val message: String, val forbidden: Boolean = false) : Load<Nothing>
}

/** Recurso carregado do servidor que se atualiza quando o feed de mudanças cita uma das [entities]. */
class Loadable<T>(
    val entities: Set<String>,
    private val scope: CoroutineScope,
    private val onAuthExpired: () -> Unit,
    private val fetch: suspend () -> T,
) {
    private val _state = MutableStateFlow<Load<T>>(Load.Idle)
    val state: StateFlow<Load<T>> = _state.asStateFlow()
    val isActive: Boolean get() = _state.value !is Load.Idle

    fun refresh() {
        scope.launch {
            if (_state.value !is Load.Ready) _state.value = Load.Loading
            try {
                _state.value = Load.Ready(fetch())
            } catch (_: AuthExpiredException) {
                onAuthExpired()
            } catch (e: ApiException) {
                _state.value = Load.Failed(e.message ?: "Erro", e.isForbidden)
            } catch (e: NetworkException) {
                val previous = (_state.value as? Load.Ready)?.data
                _state.value = if (previous != null) Load.Ready(previous, stale = true) else Load.Failed(e.message ?: "Sem conexão")
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                _state.value = Load.Failed("Resposta inesperada do servidor.")
            }
        }
    }

    fun clear() { _state.value = Load.Idle }
}

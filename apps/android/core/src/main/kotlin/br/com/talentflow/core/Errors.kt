package br.com.talentflow.core

import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive

/** Resposta de erro do servidor, já com mensagem em português. */
class ApiException(val status: Int, message: String, val detail: JsonElement? = null) : Exception(message) {
    /** HTTP 409: outro cliente alterou o registro antes. */
    val isConflict: Boolean get() = status == 409
    val isForbidden: Boolean get() = status == 403
    val currentVersion: Int? get() = (detail as? JsonObject)?.get("current_version")?.jsonPrimitive?.intOrNull
}

/** Sem rede, servidor fora do ar ou TLS inválido. Nunca simulamos dados nesse caso. */
class NetworkException(cause: Throwable? = null) :
    Exception("Não foi possível falar com o servidor. Verifique a conexão e o endereço.", cause)

/** Sessão encerrada (refresh inválido, revogado ou reutilizado): o app deve voltar ao login. */
class AuthExpiredException : Exception("Sua sessão expirou. Entre novamente.")

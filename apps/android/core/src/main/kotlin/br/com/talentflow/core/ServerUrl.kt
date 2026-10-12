package br.com.talentflow.core

import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/** Converte o endereço digitado pela pessoa na base da API v1. Nenhum domínio é presumido. */
object ServerUrl {
    /**
     * @param allowInsecure permite http:// (somente builds de depuração, para emulador/rede local).
     * @return base como "https://rh.empresa.com.br/api/v1" ou null se o endereço for inválido/inseguro.
     */
    fun toApiBase(input: String, allowInsecure: Boolean = false): String? {
        var text = input.trim().trimEnd('/')
        if (text.isEmpty()) return null
        if (!text.contains("://")) text = "https://$text"
        val url = text.toHttpUrlOrNull() ?: return null
        if (url.scheme != "https" && !(allowInsecure && url.scheme == "http")) return null
        if (url.query != null || url.fragment != null || url.username.isNotEmpty()) return null
        val path = url.encodedPath.trimEnd('/')
        val base = when {
            path.endsWith("/api/v1") -> path
            path.isEmpty() || path == "/" -> "/api/v1"
            else -> "$path/api/v1"
        }
        return url.newBuilder().encodedPath(base).build().toString().trimEnd('/')
    }
}

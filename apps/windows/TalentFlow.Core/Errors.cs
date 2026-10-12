using System.Text.Json;

namespace TalentFlow.Core;

/// <summary>Resposta de erro do servidor, com a mensagem em português.</summary>
public sealed class ApiException(int status, string message, JsonElement? detail = null) : Exception(message)
{
    public int Status { get; } = status;
    public JsonElement? Detail { get; } = detail;
    /// <summary>HTTP 409: outro cliente alterou o registro antes.</summary>
    public bool IsConflict => Status == 409;
    public bool IsForbidden => Status == 403;
    public int? CurrentVersion =>
        Detail is { ValueKind: JsonValueKind.Object } d && d.TryGetProperty("current_version", out var v) && v.TryGetInt32(out var n) ? n : null;
}

/// <summary>Sem rede, servidor fora do ar ou TLS inválido. Nunca simulamos dados nesse caso.</summary>
public sealed class NetworkException(Exception? inner = null)
    : Exception("Não foi possível falar com o servidor. Verifique a conexão e o endereço.", inner);

/// <summary>Sessão encerrada (refresh inválido, revogado ou reutilizado): voltar ao login.</summary>
public sealed class AuthExpiredException() : Exception("Sua sessão expirou. Entre novamente.");

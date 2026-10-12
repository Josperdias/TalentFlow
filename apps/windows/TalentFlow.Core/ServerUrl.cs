namespace TalentFlow.Core;

/// <summary>Converte o endereço digitado na base da API v1. Nenhum domínio é presumido.</summary>
public static class ServerUrl
{
    public static string? ToApiBase(string? input, bool allowInsecure = false)
    {
        var text = (input ?? "").Trim().TrimEnd('/');
        if (text.Length == 0) return null;
        if (!text.Contains("://")) text = "https://" + text;
        if (!Uri.TryCreate(text, UriKind.Absolute, out var url)) return null;
        if (url.Scheme != Uri.UriSchemeHttps && !(allowInsecure && url.Scheme == Uri.UriSchemeHttp)) return null;
        if (!string.IsNullOrEmpty(url.Query) || !string.IsNullOrEmpty(url.Fragment) || !string.IsNullOrEmpty(url.UserInfo)) return null;
        var path = url.AbsolutePath.TrimEnd('/');
        var basePath = path.EndsWith("/api/v1") ? path : path.Length == 0 ? "/api/v1" : path + "/api/v1";
        return new UriBuilder(url) { Path = basePath }.Uri.GetLeftPart(UriPartial.Path).TrimEnd('/');
    }
}

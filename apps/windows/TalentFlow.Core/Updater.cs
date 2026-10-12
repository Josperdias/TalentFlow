using System.Security.Cryptography;

namespace TalentFlow.Core;

/// <summary>O instalador baixado não confere com o SHA-256 anunciado pelo servidor: nunca é executado.</summary>
public sealed class UpdateIntegrityException(string message) : Exception(message);

/// <summary>
/// Atualização do aplicativo: consulta o manifesto do PRÓPRIO servidor, baixa o instalador para uma pasta temporária,
/// confere o SHA-256 (obrigatório) e devolve o caminho. Quem chama executa o instalador e encerra o app.
/// </summary>
public static class Updater
{
    /// <summary>Retorna a atualização somente se for MAIS NOVA que a versão em execução.</summary>
    public static async Task<UpdateInfo?> CheckAsync(ApiClient api, string currentVersion)
    {
        var info = await api.UpdateInfoAsync();
        return info.Available && info.Sha256.Length == 64 && Versions.IsNewer(currentVersion, info.Version) ? info : null;
    }

    public static async Task<string> DownloadAndVerifyAsync(ApiClient api, UpdateInfo info, string folder, IProgress<long>? progress = null, CancellationToken ct = default)
    {
        if (info.Sha256.Length != 64 || !info.Sha256.All(Uri.IsHexDigit)) throw new UpdateIntegrityException("O servidor não informou um SHA-256 válido para o instalador.");
        Directory.CreateDirectory(folder);
        var name = $"TalentFlow-Setup-v{info.Version}.exe";
        var target = Path.Combine(folder, name);
        var partial = target + ".part";
        try
        {
            await using (var fs = new FileStream(partial, FileMode.Create, FileAccess.Write, FileShare.None))
                await api.DownloadAsync(info.Url, fs, progress, ct);
            await using var check = File.OpenRead(partial);
            var hash = Convert.ToHexString(await SHA256.HashDataAsync(check, ct));
            if (!hash.Equals(info.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new UpdateIntegrityException("O instalador baixado não confere com o SHA-256 anunciado. A atualização foi cancelada.");
        }
        catch { TryDelete(partial); throw; }
        File.Move(partial, target, overwrite: true);
        return target;
    }

    private static void TryDelete(string path) { try { File.Delete(path); } catch { /* melhor esforço */ } }
}

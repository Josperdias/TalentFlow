using System.Security.Cryptography;
using System.Text;
using TalentFlow.Core;

namespace TalentFlow.Windows.Services;

/// <summary>
/// Guarda access/refresh token cifrados com DPAPI (escopo do usuário do Windows). Outro usuário ou outra
/// máquina não consegue ler o arquivo; se ficar ilegível, descarta e exige novo login.
/// </summary>
public sealed class DpapiTokenStore : ITokenStore
{
    private static readonly byte[] Entropy = Encoding.UTF8.GetBytes("talentflow.people.tokens.v1");
    private readonly string _path = Path.Combine(Diagnostics.Folder, "session.bin");
    private readonly object _lock = new();

    public Tokens? Load()
    {
        lock (_lock)
        {
            try
            {
                if (!File.Exists(_path)) return null;
                var plain = ProtectedData.Unprotect(File.ReadAllBytes(_path), Entropy, DataProtectionScope.CurrentUser);
                var parts = Encoding.UTF8.GetString(plain).Split('\n');
                return parts.Length == 2 ? new Tokens(parts[0], parts[1]) : null;
            }
            catch (Exception e) when (e is CryptographicException or IOException or UnauthorizedAccessException)
            {
                TryDelete(); return null;
            }
        }
    }

    public void Save(Tokens? tokens)
    {
        lock (_lock)
        {
            if (tokens is null) { TryDelete(); return; }
            Directory.CreateDirectory(Diagnostics.Folder);
            var sealedBytes = ProtectedData.Protect(Encoding.UTF8.GetBytes($"{tokens.Access}\n{tokens.Refresh}"), Entropy, DataProtectionScope.CurrentUser);
            File.WriteAllBytes(_path, sealedBytes);
        }
    }

    private void TryDelete() { try { File.Delete(_path); } catch { /* ignore */ } }
}

namespace TalentFlow.Windows.Services;

/// <summary>Registro local simples (sem dados pessoais nem tokens) para suporte.</summary>
public static class Diagnostics
{
    public static string Folder { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "TalentFlow");

    public static void Log(string where, Exception? e = null)
    {
        try
        {
            Directory.CreateDirectory(Folder);
            var path = Path.Combine(Folder, "talentflow.log");
            if (File.Exists(path) && new FileInfo(path).Length > 512_000) File.Delete(path);
            File.AppendAllText(path, $"{DateTime.UtcNow:O} {where} {e?.GetType().Name} {e?.Message}\n");
        }
        catch { /* log nunca pode causar falha */ }
    }
}

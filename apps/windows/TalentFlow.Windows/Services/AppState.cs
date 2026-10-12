using Microsoft.UI.Xaml;
using TalentFlow.Core;

namespace TalentFlow.Windows.Services;

public enum Connection { Connecting, Online, Offline }

/// <summary>Resultado de uma escrita; conflito (409) tem tratamento próprio e nunca sobrescreve em silêncio.</summary>
public sealed record ActionResult(bool Ok, bool Conflict = false, string Message = "");

/// <summary>Sessão, cliente da API e sincronização. Uma instância por processo.</summary>
public static class AppState
{
    private static readonly string SettingsFile = Path.Combine(Diagnostics.Folder, "server.txt");
    private static readonly DpapiTokenStore Tokens = new();
    private static DispatcherTimer? _timer;
    private static ChangeFeed? _feed;

    public static ApiClient? Api { get; private set; }
    public static User? User { get; private set; }
    public static string? ServerBase { get; private set; }
    public static string? UpdateNotice { get; private set; }
    /// <summary>Versão mais nova publicada no PRÓPRIO servidor (null = em dia ou nada publicado).</summary>
    public static UpdateInfo? PendingUpdate { get; private set; }
    public static event Action? UpdateChanged;
    public static Connection Connection { get; private set; } = Connection.Connecting;
    public static string Version { get; } =
        System.Reflection.Assembly.GetExecutingAssembly().GetCustomAttributes(typeof(System.Reflection.AssemblyInformationalVersionAttribute), false)
            .OfType<System.Reflection.AssemblyInformationalVersionAttribute>().FirstOrDefault()?.InformationalVersion.Split('+')[0] ?? "0.0.0";

    /// <summary>Entidades alteradas por outros clientes (job, application, ...). Chamado na thread da interface.</summary>
    public static event Action<HashSet<string>>? Changed;
    public static event Action? ConnectionChanged;
    public static event Action? SignedOut;

    public static void LoadSettings()
    {
        try { ServerBase = File.Exists(SettingsFile) ? File.ReadAllText(SettingsFile).Trim() : null; } catch { ServerBase = null; }
        if (!string.IsNullOrEmpty(ServerBase)) Api = new ApiClient(ServerBase, Tokens, "windows", Environment.MachineName);
    }

    /// <summary>Valida o endereço digitado e confere se a API responde antes de guardar.</summary>
    public static async Task<string?> SetServerAsync(string input)
    {
        var baseUrl = ServerUrl.ToApiBase(input);
        if (baseUrl is null) return "Endereço inválido. Use https:// e o endereço do seu servidor.";
        try
        {
            var candidate = new ApiClient(baseUrl, Tokens, "windows", Environment.MachineName);
            await candidate.HealthAsync();
            Directory.CreateDirectory(Diagnostics.Folder);
            File.WriteAllText(SettingsFile, baseUrl);
            ServerBase = baseUrl; Api = candidate;
            return null;
        }
        catch (NetworkException) { return "Não foi possível alcançar a API nesse endereço."; }
        catch (Exception) { return "O endereço respondeu, mas não parece ser a API do TalentFlow."; }
    }

    public static async Task ChangeServerAsync()
    {
        if (Api is not null) await Api.LogoutAsync();
        try { File.Delete(SettingsFile); } catch { /* ignore */ }
        Stop(); Api = null; ServerBase = null; User = null;
    }

    /// <summary>Retoma a sessão salva. Null = precisa entrar.</summary>
    public static async Task<(User? User, string? Error)> TryRestoreAsync()
    {
        if (Api is null || !Api.IsSignedIn) return (null, null);
        try { User = await Api.MeAsync(); await CheckVersionAsync(); return (User, null); }
        catch (AuthExpiredException) { return (null, "Sua sessão expirou. Entre novamente."); }
        catch (ApiException e) when (e.Status == 401) { return (null, null); }
        catch (NetworkException e) { return (null, e.Message); }
        catch (ApiException e) { return (null, e.Message); }
    }

    public static async Task<string?> LoginAsync(string email, string password)
    {
        try { User = await Api!.LoginAsync(email, password); await CheckVersionAsync(); return null; }
        catch (ApiException e) { return e.Message; }
        catch (NetworkException e) { return e.Message; }
    }

    public static async Task LogoutAsync()
    {
        Stop();
        if (Api is not null) await Api.LogoutAsync();
        User = null; SignedOut?.Invoke();
    }

    private static async Task CheckVersionAsync()
    {
        try
        {
            var min = (await Api!.HealthAsync()).MinClientVersion?.GetValueOrDefault("windows");
            UpdateNotice = min is not null && Versions.IsBelow(Version, min)
                ? $"Este aplicativo ({Version}) está abaixo da versão mínima {min} exigida pelo servidor. Baixe a versão mais recente." : null;
        }
        catch { /* aviso é opcional */ }
    }

    // ---- atualização do aplicativo (instalador servido pelo seu servidor, SHA-256 obrigatório) ----
    private static DispatcherTimer? _updateTimer;

    /// <summary>Consulta o servidor; retorna true se há versão mais nova que a em execução.</summary>
    public static async Task<bool> CheckUpdateAsync()
    {
        try { PendingUpdate = Api is null ? null : await Updater.CheckAsync(Api, Version); }
        catch (AuthExpiredException) { }
        catch (Exception e) when (e is ApiException or NetworkException) { /* sem rede: mantém o que já sabíamos */ }
        UpdateChanged?.Invoke();
        return PendingUpdate is not null;
    }

    /// <summary>Baixa, confere o SHA-256, abre o instalador e encerra o aplicativo. Retorna uma mensagem se algo falhar.</summary>
    public static async Task<string?> InstallUpdateAsync(IProgress<long>? progress = null)
    {
        var info = PendingUpdate; if (info is null || Api is null) return "Nenhuma atualização pendente.";
        try
        {
            var path = await Updater.DownloadAndVerifyAsync(Api, info, Path.Combine(Path.GetTempPath(), "TalentFlowUpdate"), progress);
            // /RELAUNCH=1: o instalador reabre o aplicativo ao terminar. Os dados e a sessão (DPAPI) ficam em %LOCALAPPDATA% e são preservados.
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(path, "/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /RELAUNCH=1") { UseShellExecute = true });
            Application.Current.Exit();
            return null;
        }
        catch (UpdateIntegrityException e) { Diagnostics.Log("UpdateIntegrity", e); return e.Message; }
        catch (Exception e) when (e is ApiException or NetworkException) { return e.Message; }
        catch (Exception e) { Diagnostics.Log("InstallUpdate", e); return "Não foi possível iniciar a atualização: " + e.Message; }
    }

    // ---- sincronização ----
    public static void StartSync()
    {
        Stop();
        if (Api is null || User is null || User.Role == "candidate") { SetConnection(Connection.Online); return; }
        _ = CheckUpdateAsync();
        _updateTimer?.Stop();
        _updateTimer = new DispatcherTimer { Interval = TimeSpan.FromHours(6) };
        _updateTimer.Tick += async (_, _) => await CheckUpdateAsync();
        _updateTimer.Start();
        _feed = new ChangeFeed(Api);
        _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(5) };
        _timer.Tick += async (_, _) => await PollAsync();
        _timer.Start();
        _ = PollAsync();
    }

    /// <summary>Chamado por páginas quando a API informa que a sessão acabou.</summary>
    public static void ExpireSession() { Stop(); User = null; SignedOut?.Invoke(); }

    public static void Stop() { _timer?.Stop(); _timer = null; _feed = null; _updateTimer?.Stop(); _updateTimer = null; }

    public static Task PokeAsync() => PollAsync();

    private static async Task PollAsync()
    {
        var feed = _feed; if (feed is null) return;
        try
        {
            var changed = await feed.PollAsync();
            SetConnection(Connection.Online);
            if (changed.Count > 0) Changed?.Invoke(changed);
        }
        catch (AuthExpiredException) { Stop(); User = null; SignedOut?.Invoke(); }
        catch (Exception) { SetConnection(Connection.Offline); }
    }

    private static void SetConnection(Connection c)
    {
        if (Connection == c) return;
        Connection = c; ConnectionChanged?.Invoke();
    }

    /// <summary>Executa uma escrita e traduz as falhas em <see cref="ActionResult"/>.</summary>
    public static async Task<ActionResult> ActAsync(Func<Task> action)
    {
        try { await action(); return new ActionResult(true); }
        catch (ApiException e) { return new ActionResult(false, e.IsConflict, e.Message); }
        catch (NetworkException e) { return new ActionResult(false, false, e.Message); }
        catch (AuthExpiredException) { Stop(); User = null; SignedOut?.Invoke(); return new ActionResult(false, false, "Sessão expirada"); }
    }
}

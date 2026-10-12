using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace TalentFlow.Core;

public sealed record Tokens(string Access, string Refresh);

/// <summary>Onde os tokens ficam. No Windows: cifrados com DPAPI (escopo do usuário atual).</summary>
public interface ITokenStore
{
    Tokens? Load();
    void Save(Tokens? tokens);
}

public sealed class MemoryTokenStore : ITokenStore
{
    private Tokens? _value;
    public Tokens? Load() => _value;
    public void Save(Tokens? tokens) => _value = tokens;
}

/// <summary>
/// Cliente da API v1 (apenas HTTPS; o PostgreSQL nunca é acessado diretamente).
/// 401 -> UM refresh rotativo e repete; refresh recusado apaga tokens e lança <see cref="AuthExpiredException"/>.
/// Mutations enviam If-Match com a versão que a pessoa viu; 409 vira <see cref="ApiException.IsConflict"/>.
/// </summary>
public sealed class ApiClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _http;
    private readonly ITokenStore _store;
    private readonly string _clientName;
    private readonly string _device;
    private readonly SemaphoreSlim _refreshLock = new(1, 1);

    public string ApiBase { get; }
    public bool IsSignedIn => _store.Load() is not null;

    public ApiClient(string apiBase, ITokenStore store, string clientName = "windows", string device = "", HttpMessageHandler? handler = null)
    {
        ApiBase = apiBase.TrimEnd('/');
        _store = store; _clientName = clientName; _device = device;
        _http = handler is null ? new HttpClient() : new HttpClient(handler);
        _http.Timeout = TimeSpan.FromSeconds(25);
    }

    public async Task<User> LoginAsync(string email, string password, CancellationToken ct = default)
    {
        var body = new JsonObject { ["email"] = email.Trim(), ["password"] = password, ["client"] = _clientName, ["device"] = _device };
        var text = await ExecuteAsync("POST", "/auth/token", body, null, authenticated: false, ct: ct);
        var parsed = Deserialize<TokenResponse>(text);
        _store.Save(new Tokens(parsed.AccessToken, parsed.RefreshToken));
        return parsed.User;
    }

    public async Task LogoutAsync()
    {
        try { await ExecuteAsync("POST", "/auth/logout", new JsonObject(), null, retryOnAuth: false); }
        catch { /* sair deve sempre limpar o aparelho, mesmo sem rede */ }
        finally { _store.Save(null); }
    }

    public async Task<HealthInfo> HealthAsync(CancellationToken ct = default) =>
        Deserialize<HealthInfo>(await ExecuteAsync("GET", "/health", null, null, authenticated: false, ct: ct));

    public async Task<T> GetAsync<T>(string path, CancellationToken ct = default) =>
        Deserialize<T>(await ExecuteAsync("GET", path, null, null, ct: ct));

    public async Task<T> PostAsync<T>(string path, JsonObject body, int? ifMatch = null, CancellationToken ct = default) =>
        Deserialize<T>(await ExecuteAsync("POST", path, body, ifMatch, ct: ct));

    public async Task<T> PatchAsync<T>(string path, JsonObject body, int ifMatch, CancellationToken ct = default) =>
        Deserialize<T>(await ExecuteAsync("PATCH", path, body, ifMatch, ct: ct));

    private static T Deserialize<T>(string text) =>
        JsonSerializer.Deserialize<T>(text, JsonOptions) ?? throw new ApiException(500, "Resposta vazia do servidor.");

    internal async Task<string> ExecuteAsync(string method, string path, JsonObject? body, int? ifMatch,
        bool authenticated = true, bool retryOnAuth = true, CancellationToken ct = default)
    {
        var used = _store.Load()?.Access;
        var first = await SendAsync(method, path, body, ifMatch, authenticated ? used : null, ct);
        if (first.Status == 401 && authenticated && retryOnAuth)
        {
            if (!await RefreshAsync(used, ct)) throw new AuthExpiredException();
            var second = await SendAsync(method, path, body, ifMatch, _store.Load()?.Access, ct);
            if (second.Status == 401) { _store.Save(null); throw new AuthExpiredException(); }
            return Unwrap(second);
        }
        return Unwrap(first);
    }

    /// <summary>Evita refresh em paralelo: quem chegar depois reutiliza o token novo.</summary>
    private async Task<bool> RefreshAsync(string? accessThatFailed, CancellationToken ct)
    {
        await _refreshLock.WaitAsync(ct);
        try
        {
            var current = _store.Load();
            if (current is null) return false;
            if (current.Access != accessThatFailed) return true; // outra chamada já renovou
            var r = await SendAsync("POST", "/auth/refresh", new JsonObject { ["refresh_token"] = current.Refresh }, null, null, ct);
            if (r.Status != 200) { _store.Save(null); return false; }
            var parsed = Deserialize<RefreshResponse>(r.Body);
            _store.Save(new Tokens(parsed.AccessToken, parsed.RefreshToken));
            return true;
        }
        finally { _refreshLock.Release(); }
    }

    private sealed record Raw(int Status, string Body);

    private static string Unwrap(Raw r)
    {
        if (r.Status is >= 200 and < 300) return r.Body;
        JsonElement? detail = null;
        string? message = null;
        try
        {
            using var doc = JsonDocument.Parse(r.Body);
            if (doc.RootElement.ValueKind == JsonValueKind.Object && doc.RootElement.TryGetProperty("detail", out var d))
            {
                detail = d.Clone();
                message = d.ValueKind switch
                {
                    JsonValueKind.String => d.GetString(),
                    JsonValueKind.Object when d.TryGetProperty("message", out var m) => m.GetString(),
                    JsonValueKind.Array => "Revise os campos informados.",
                    _ => null
                };
            }
        }
        catch (JsonException) { /* corpo não-JSON */ }
        throw new ApiException(r.Status, message ?? $"Erro {r.Status}", detail);
    }

    private async Task<Raw> SendAsync(string method, string path, JsonObject? body, int? ifMatch, string? access, CancellationToken ct)
    {
        using var req = new HttpRequestMessage(new HttpMethod(method), ApiBase + path);
        req.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        if (access is not null) req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", access);
        if (ifMatch is not null) req.Headers.TryAddWithoutValidation("If-Match", ifMatch.Value.ToString());
        if (body is not null) req.Content = new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json");
        else if (method != "GET") req.Content = new StringContent("", Encoding.UTF8, "application/json");
        try
        {
            using var res = await _http.SendAsync(req, ct);
            return new Raw((int)res.StatusCode, await res.Content.ReadAsStringAsync(ct));
        }
        catch (HttpRequestException e) { throw new NetworkException(e); }
        catch (TaskCanceledException e) when (!ct.IsCancellationRequested) { throw new NetworkException(e); }
    }
}

/// <summary>Operações de domínio: os mesmos endpoints usados pelo site e pelo Android.</summary>
public static class Api
{
    public static Task<Dashboard> DashboardAsync(this ApiClient c) => c.GetAsync<Dashboard>("/dashboard");
    public static Task<Trend> TrendAsync(this ApiClient c) => c.GetAsync<Trend>("/dashboard/trend");
    public static Task<Insights> InsightsAsync(this ApiClient c) => c.GetAsync<Insights>("/workforce/insights");
    public static Task<List<Job>> JobsAsync(this ApiClient c, string query = "") => c.GetAsync<List<Job>>("/jobs?q=" + Uri.EscapeDataString(query));
    public static Task<JobDetail> JobDetailAsync(this ApiClient c, int id) => c.GetAsync<JobDetail>($"/jobs/{id}");

    public static Task<Job> CreateJobAsync(this ApiClient c, string title, string department, string location, string status)
    {
        var body = new JsonObject { ["title"] = title, ["status"] = status };
        if (!string.IsNullOrWhiteSpace(department)) body["department"] = department;
        if (!string.IsNullOrWhiteSpace(location)) body["location"] = location;
        return c.PostAsync<Job>("/jobs", body);
    }

    public static Task<Job> UpdateJobTitleAsync(this ApiClient c, Job job, string title) =>
        c.PatchAsync<Job>($"/jobs/{job.Id}", new JsonObject { ["title"] = title }, job.Version);

    public static Task<MoveResult> MoveApplicationAsync(this ApiClient c, ApplicationRow app, int stageId, string reason = "") =>
        c.PostAsync<MoveResult>($"/applications/{app.Id}/move", new JsonObject { ["stage_id"] = stageId, ["reason"] = reason }, app.Version);

    public static Task<List<Candidate>> CandidatesAsync(this ApiClient c, string query = "") => c.GetAsync<List<Candidate>>("/candidates?q=" + Uri.EscapeDataString(query));
    public static Task<List<Employee>> EmployeesAsync(this ApiClient c) => c.GetAsync<List<Employee>>("/lifecycle/employees");
    public static Task<List<Plan>> PlansAsync(this ApiClient c, string status = "") => c.GetAsync<List<Plan>>("/workforce/plans?status=" + status);

    public static Task<Plan> SetPlanActionAsync(this ApiClient c, Plan plan, int index, bool done, string evidence = "") =>
        c.PostAsync<Plan>($"/workforce/plans/{plan.Id}/action",
            new JsonObject { ["index"] = index, ["done"] = done, ["evidence"] = evidence }, plan.Version);

    public static Task<List<Leave>> LeavesAsync(this ApiClient c, string status = "") => c.GetAsync<List<Leave>>("/workforce/leaves?status=" + status);

    public static Task<Leave> DecideLeaveAsync(this ApiClient c, int id, bool approved) =>
        c.PostAsync<Leave>($"/workforce/leaves/{id}/decide", new JsonObject { ["decision"] = approved ? "approved" : "rejected" });

    public static Task<Portal> PortalAsync(this ApiClient c) => c.GetAsync<Portal>("/portal");
    public static Task<List<SessionInfo>> SessionsAsync(this ApiClient c) => c.GetAsync<List<SessionInfo>>("/auth/sessions");
    public static async Task<int> RevokeOtherSessionsAsync(this ApiClient c) =>
        (await c.PostAsync<RevokeResult>("/auth/sessions/revoke-others", new JsonObject())).Revoked;
    public static async Task<User> MeAsync(this ApiClient c) => (await c.GetAsync<MeEnvelope>("/me")).User;
}

/// <summary>Acompanha /changes como dica de invalidação; a UI rebusca pelos endpoints normais (com RBAC).</summary>
public sealed class ChangeFeed(ApiClient api)
{
    private long? _cursor;

    public async Task<HashSet<string>> PollAsync(CancellationToken ct = default)
    {
        _cursor ??= (await api.GetAsync<CursorResponse>("/changes/cursor", ct)).Cursor;
        var changed = new HashSet<string>();
        Changes page;
        do
        {
            page = await api.GetAsync<Changes>($"/changes?after={_cursor}&limit=200", ct);
            foreach (var e in page.Entities) changed.Add(e);
            _cursor = page.Cursor;
        } while (page.HasMore);
        return changed;
    }

    public void Reset() => _cursor = null;
}

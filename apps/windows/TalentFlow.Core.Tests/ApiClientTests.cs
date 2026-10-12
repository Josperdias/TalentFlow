using System.Net;
using System.Text;
using System.Text.Json.Nodes;
using TalentFlow.Core;
using Xunit;

namespace TalentFlow.Core.Tests;

/// <summary>Servidor simulado: responde na ordem e guarda as requisições para conferência.</summary>
internal sealed class QueueHandler : HttpMessageHandler
{
    public readonly Queue<Func<HttpResponseMessage>> Responses = new();
    public readonly List<(HttpMethod Method, string Path, string? Auth, string? IfMatch, string Body)> Requests = new();
    public bool Offline { get; set; }

    public void Enqueue(HttpStatusCode code, string json) =>
        Responses.Enqueue(() => new HttpResponseMessage(code) { Content = new StringContent(json, Encoding.UTF8, "application/json") });

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct)
    {
        if (Offline) throw new HttpRequestException("sem rede");
        var body = request.Content is null ? "" : await request.Content.ReadAsStringAsync(ct);
        request.Headers.TryGetValues("If-Match", out var im);
        Requests.Add((request.Method, request.RequestUri!.AbsolutePath + request.RequestUri.Query,
            request.Headers.Authorization?.ToString(), im?.FirstOrDefault(), body));
        return Responses.Dequeue()();
    }
}

public class ApiClientTests
{
    private const string UserJson = """{"id":1,"name":"Marina","email":"m@x","role":"admin","company_id":1,"company":"Nexa"}""";
    private static string TokenBody(string a, string r) => $$"""{"access_token":"{{a}}","refresh_token":"{{r}}","user":{{UserJson}}}""";

    private static (ApiClient api, QueueHandler h, MemoryTokenStore store) Make()
    {
        var h = new QueueHandler(); var store = new MemoryTokenStore();
        return (new ApiClient("https://x.test/api/v1", store, "windows", "PC de teste", h), h, store);
    }

    [Fact]
    public async Task Login_guarda_tokens_e_envia_client_sem_Authorization()
    {
        var (api, h, store) = Make();
        h.Enqueue(HttpStatusCode.OK, TokenBody("A1", "R1"));
        var user = await api.LoginAsync(" m@x ", "senha");
        Assert.Equal("Marina", user.Name);
        Assert.Equal(new Tokens("A1", "R1"), store.Load());
        Assert.Null(h.Requests[0].Auth);
        Assert.Contains("\"client\":\"windows\"", h.Requests[0].Body);
    }

    [Fact]
    public async Task Senha_errada_vira_ApiException_e_nao_guarda_tokens()
    {
        var (api, h, store) = Make();
        h.Enqueue(HttpStatusCode.Unauthorized, """{"detail":"Credenciais inválidas"}""");
        var e = await Assert.ThrowsAsync<ApiException>(() => api.LoginAsync("a@b", "x"));
        Assert.Equal(401, e.Status); Assert.Equal("Credenciais inválidas", e.Message);
        Assert.Null(store.Load());
    }

    [Fact]
    public async Task Status_401_faz_refresh_uma_vez_e_repete_com_o_token_novo()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("velho", "R1"));
        h.Enqueue(HttpStatusCode.Unauthorized, """{"detail":"Sessão expirada"}""");
        h.Enqueue(HttpStatusCode.OK, """{"access_token":"novo","refresh_token":"R2"}""");
        h.Enqueue(HttpStatusCode.OK, "[]");
        Assert.Empty(await api.JobsAsync());
        Assert.Equal("Bearer velho", h.Requests[0].Auth);
        Assert.EndsWith("/auth/refresh", h.Requests[1].Path); Assert.Contains("R1", h.Requests[1].Body);
        Assert.Equal("Bearer novo", h.Requests[2].Auth);
        Assert.Equal(new Tokens("novo", "R2"), store.Load());
    }

    [Fact]
    public async Task Refresh_recusado_apaga_tokens_e_exige_login()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("velho", "R1"));
        h.Enqueue(HttpStatusCode.Unauthorized, """{"detail":"Sessão expirada"}""");
        h.Enqueue(HttpStatusCode.Unauthorized, """{"detail":"Refresh token reutilizado"}""");
        await Assert.ThrowsAsync<AuthExpiredException>(() => api.JobsAsync());
        Assert.Null(store.Load());
    }

    [Fact]
    public async Task Patch_envia_IfMatch_e_409_expoe_a_versao_atual()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R"));
        h.Enqueue(HttpStatusCode.Conflict, """{"detail":{"message":"O registro foi alterado por outra sessão.","current_version":7}}""");
        var e = await Assert.ThrowsAsync<ApiException>(() => api.UpdateJobTitleAsync(new Job(5, "TF-00005", "Antiga", Version: 3), "Nova"));
        Assert.True(e.IsConflict); Assert.Equal(7, e.CurrentVersion);
        Assert.Equal("3", h.Requests[0].IfMatch); Assert.Equal(HttpMethod.Patch, h.Requests[0].Method);
    }

    [Fact]
    public async Task Mover_candidatura_envia_a_versao_da_candidatura()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R"));
        h.Enqueue(HttpStatusCode.OK, """{"ok":true,"stage":"Triagem","status":"active","version":4}""");
        var app = new ApplicationRow(9, 2, 10, "Novos", "active", 80, 3, new Candidate(1, "Ana"));
        var r = await api.MoveApplicationAsync(app, 11);
        Assert.Equal(4, r.Version); Assert.Equal("3", h.Requests[0].IfMatch); Assert.EndsWith("/applications/9/move", h.Requests[0].Path);
    }

    [Fact]
    public async Task Falha_de_rede_vira_NetworkException()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R")); h.Offline = true;
        await Assert.ThrowsAsync<NetworkException>(() => api.JobsAsync());
    }

    [Fact]
    public async Task Erro_de_validacao_em_lista_vira_mensagem_generica()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R"));
        h.Enqueue(HttpStatusCode.UnprocessableEntity, """{"detail":[{"msg":"too short"}]}""");
        var e = await Assert.ThrowsAsync<ApiException>(() => api.CreateJobAsync("a", "", "", "open"));
        Assert.Equal("Revise os campos informados.", e.Message);
    }

    [Fact]
    public async Task Logout_limpa_tokens_mesmo_sem_rede()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R")); h.Offline = true;
        await api.LogoutAsync();
        Assert.Null(store.Load());
    }

    [Fact]
    public async Task Feed_busca_cursor_e_depois_so_o_que_mudou()
    {
        var (api, h, store) = Make(); store.Save(new Tokens("A", "R"));
        h.Enqueue(HttpStatusCode.OK, """{"cursor":10}""");
        h.Enqueue(HttpStatusCode.OK, """{"cursor":12,"has_more":false,"entities":["job","application"]}""");
        var feed = new ChangeFeed(api);
        Assert.Equal(new HashSet<string> { "job", "application" }, await feed.PollAsync());
        Assert.EndsWith("/changes/cursor", h.Requests[0].Path); Assert.EndsWith("/changes?after=10&limit=200", h.Requests[1].Path);
        h.Enqueue(HttpStatusCode.OK, """{"cursor":12,"has_more":false,"entities":[]}""");
        Assert.Empty(await feed.PollAsync());
        Assert.EndsWith("/changes?after=12&limit=200", h.Requests[2].Path);
    }
}

public class ServerUrlTests
{
    [Theory]
    [InlineData("rh.empresa.com.br", "https://rh.empresa.com.br/api/v1")]
    [InlineData(" https://rh.empresa.com.br/ ", "https://rh.empresa.com.br/api/v1")]
    [InlineData("https://rh.empresa.com.br/api/v1/", "https://rh.empresa.com.br/api/v1")]
    [InlineData("https://x.com/talentflow", "https://x.com/talentflow/api/v1")]
    public void Normaliza_enderecos_validos(string input, string expected) => Assert.Equal(expected, ServerUrl.ToApiBase(input));

    [Theory]
    [InlineData("")] [InlineData("http://rh.empresa.com.br")] [InlineData("https://user:pw@x.com")] [InlineData("https://x.com/?a=1")]
    public void Recusa_http_e_entradas_invalidas(string input) => Assert.Null(ServerUrl.ToApiBase(input));

    [Fact]
    public void Permite_http_so_com_autorizacao_explicita() => Assert.Equal("http://127.0.0.1:8000/api/v1", ServerUrl.ToApiBase("http://127.0.0.1:8000", allowInsecure: true));

    [Fact]
    public void Compara_versoes_ignorando_sufixo_rc()
    {
        Assert.True(Versions.IsBelow("1.2.9", "1.3.0")); Assert.False(Versions.IsBelow("1.3.0-rc.1", "1.3.0"));
        Assert.False(Versions.IsBelow("2.0.0", "1.9.9")); Assert.True(Versions.IsBelow("1.0", "1.0.1"));
    }
}

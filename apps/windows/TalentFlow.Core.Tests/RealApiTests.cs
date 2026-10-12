using TalentFlow.Core;
using Xunit;

namespace TalentFlow.Core.Tests;

/// <summary>
/// Integração contra a API REAL (FastAPI + PostgreSQL). Só roda com TF_API_URL, ex.:
///   TF_API_URL=http://127.0.0.1:8000 dotnet test --filter RealApi
/// Dois "aparelhos" provam sincronização e conflito entre clientes.
/// </summary>
public class RealApiTests
{
    private const string Password = "Demo@2026!";
    private static readonly string? Base = ServerUrl.ToApiBase(Environment.GetEnvironmentVariable("TF_API_URL"), allowInsecure: true);
    private static ApiClient Client(string device, MemoryTokenStore? store = null) => new(Base!, store ?? new MemoryTokenStore(), "windows", device);

    [SkippableFact]
    public async Task Login_real_leitura_autorizada_e_isolamento_entre_empresas()
    {
        Skip.If(Base is null, "TF_API_URL não definido");
        var nexa = Client("A"); var orbe = Client("B");
        Assert.Equal("admin", (await nexa.LoginAsync("admin@nexa.demo", Password)).Role);
        await orbe.LoginAsync("admin@orbe.demo", Password);
        var nexaJobs = await nexa.JobsAsync(); var orbeJobs = await orbe.JobsAsync();
        Assert.NotEmpty(nexaJobs);
        Assert.Empty(nexaJobs.Select(j => j.Id).Intersect(orbeJobs.Select(j => j.Id)));
        var e = await Assert.ThrowsAsync<ApiException>(() => orbe.JobDetailAsync(nexaJobs[0].Id));
        Assert.Equal(404, e.Status);
        Assert.False(string.IsNullOrEmpty((await nexa.HealthAsync()).ApiVersion));
        var trend = await nexa.TrendAsync();
        Assert.NotEmpty(trend.Points);
        Assert.Equal(trend.TotalApplications, trend.Points.Sum(p => p.Applications));
    }

    [SkippableFact]
    public async Task Criar_no_aparelho_A_aparece_no_B_e_conflito_e_detectado()
    {
        Skip.If(Base is null, "TF_API_URL não definido");
        var a = Client("A"); var b = Client("B");
        await a.LoginAsync("admin@nexa.demo", Password); await b.LoginAsync("recrutador@nexa.demo", Password);
        var feedB = new ChangeFeed(b); await feedB.PollAsync();
        var created = await a.CreateJobAsync($"Vaga criada no Windows {DateTime.UtcNow.Ticks}", "Tecnologia", "Remoto", "open");
        Assert.Contains("job", await feedB.PollAsync());
        Assert.Contains(await b.JobsAsync(), j => j.Id == created.Id);
        var seenByB = (await b.JobDetailAsync(created.Id)).Job;
        await b.UpdateJobTitleAsync(seenByB, $"Editada no B {DateTime.UtcNow.Ticks}");
        var e = await Assert.ThrowsAsync<ApiException>(() => a.UpdateJobTitleAsync(created, "Edição do A que não pode vencer"));
        Assert.True(e.IsConflict); Assert.True(e.CurrentVersion > created.Version);
        Assert.StartsWith("Editada no B", (await a.JobDetailAsync(created.Id)).Job.Title);
    }

    [SkippableFact]
    public async Task Refresh_real_rotaciona_e_logout_limpa_a_sessao()
    {
        Skip.If(Base is null, "TF_API_URL não definido");
        var store = new MemoryTokenStore(); var c = Client("PC", store);
        await c.LoginAsync("gestor@nexa.demo", Password);
        var before = store.Load()!;
        store.Save(before with { Access = "token-invalido" }); // força 401 -> refresh real
        Assert.True((await c.DashboardAsync()).Metrics.JobsOpen >= 0);
        Assert.NotEqual(before.Refresh, store.Load()!.Refresh);
        await c.LogoutAsync();
        Assert.Null(store.Load());
    }

    /// <summary>Cadeia completa de atualização contra a API real: manifesto -> download autenticado -> SHA-256. Exige TF_EXPECT_UPDATE=1 (o CI prepara o diretório).</summary>
    [SkippableFact]
    public async Task Atualizacao_real_manifesto_download_e_sha256()
    {
        Skip.If(Base is null || Environment.GetEnvironmentVariable("TF_EXPECT_UPDATE") != "1", "TF_API_URL/TF_EXPECT_UPDATE não definidos");
        var c = Client("U");
        await c.LoginAsync("admin@nexa.demo", Password);
        var info = await Updater.CheckAsync(c, "1.0.0");
        Assert.NotNull(info);
        Assert.Equal("99.0.0", info!.Version);
        Assert.Null(await Updater.CheckAsync(c, "99.0.0"));   // já está na versão publicada
        var dir = Path.Combine(Path.GetTempPath(), "tf-real-upd-" + Guid.NewGuid().ToString("N"));
        var file = await Updater.DownloadAndVerifyAsync(c, info, dir);
        Assert.Equal(info.Size, new FileInfo(file).Length);
    }
}

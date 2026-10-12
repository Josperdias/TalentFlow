using System.Net;
using System.Security.Cryptography;
using System.Text;
using TalentFlow.Core;
using Xunit;

namespace TalentFlow.Core.Tests;

public class UpdaterTests
{
    [Theory]
    [InlineData("1.3.0-rc.1", "1.3.0-rc.2", true)]
    [InlineData("1.3.0-rc.2", "1.3.0-rc.10", true)]
    [InlineData("1.3.0-rc.1", "1.3.0", true)]
    [InlineData("1.3.0", "1.3.0-rc.9", false)]
    [InlineData("1.3.0", "1.3.0", false)]
    [InlineData("1.3.9", "1.4.0", true)]
    [InlineData("2.0.0", "1.99.99", false)]
    [InlineData("1.3.0+build5", "1.3.0", false)]
    public void Precedencia_semantica(string atual, string candidata, bool maisNova) =>
        Assert.Equal(maisNova, Versions.IsNewer(atual, candidata));

    private static string Sha(byte[] b) => Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    private static string Temp() => Path.Combine(Path.GetTempPath(), "tf-upd-" + Guid.NewGuid().ToString("N"));

    private static (ApiClient api, QueueHandler h) Make(string apiBase = "https://x.test/api/v1")
    {
        var h = new QueueHandler(); var store = new MemoryTokenStore(); store.Save(new Tokens("acc", "ref"));
        return (new ApiClient(apiBase, store, "windows", "PC", h), h);
    }

    [Fact]
    public async Task Baixa_confere_o_sha256_e_entrega_o_arquivo()
    {
        var blob = Encoding.UTF8.GetBytes(new string('M', 5000));
        var (api, h) = Make();
        h.Responses.Enqueue(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(blob) });
        var info = new UpdateInfo(true, "1.4.0", "/api/v1/client-updates/windows/download/TalentFlow-Setup-v1.4.0.exe", Sha(blob), blob.Length);
        var dir = Temp();
        var path = await Updater.DownloadAndVerifyAsync(api, info, dir);
        Assert.Equal(blob, await File.ReadAllBytesAsync(path));
        Assert.EndsWith("TalentFlow-Setup-v1.4.0.exe", path);
        Assert.Equal("/api/v1/client-updates/windows/download/TalentFlow-Setup-v1.4.0.exe", h.Requests[0].Path);
        Assert.Equal("Bearer acc", h.Requests[0].Auth);
        Assert.Empty(Directory.GetFiles(dir, "*.part"));
    }

    [Fact]
    public async Task Sha256_diferente_cancela_e_nao_deixa_arquivo()
    {
        var (api, h) = Make();
        h.Responses.Enqueue(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(Encoding.UTF8.GetBytes("adulterado")) });
        var info = new UpdateInfo(true, "1.4.0", "/api/v1/client-updates/windows/download/x.exe", new string('a', 64), 10);
        var dir = Temp();
        await Assert.ThrowsAsync<UpdateIntegrityException>(() => Updater.DownloadAndVerifyAsync(api, info, dir));
        Assert.Empty(Directory.GetFiles(dir));
    }

    [Fact]
    public async Task Sem_sha256_valido_nem_baixa()
    {
        var (api, h) = Make();
        var info = new UpdateInfo(true, "1.4.0", "/api/v1/client-updates/windows/download/x.exe", "", 10);
        await Assert.ThrowsAsync<UpdateIntegrityException>(() => Updater.DownloadAndVerifyAsync(api, info, Temp()));
        Assert.Empty(h.Requests);
    }

    [Fact]
    public async Task Host_diferente_exige_https_e_nunca_recebe_o_token()
    {
        var (api, h) = Make();
        var http = new UpdateInfo(true, "1.4.0", "http://cdn.exemplo.test/setup.exe", new string('b', 64), 1);
        await Assert.ThrowsAsync<ApiException>(() => Updater.DownloadAndVerifyAsync(api, http, Temp()));
        Assert.Empty(h.Requests);

        var blob = new byte[] { 1, 2, 3 };
        h.Responses.Enqueue(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(blob) });
        var https = new UpdateInfo(true, "1.4.0", "https://cdn.exemplo.test/setup.exe", Sha(blob), 3);
        await Updater.DownloadAndVerifyAsync(api, https, Temp());
        Assert.Null(h.Requests[0].Auth);
    }

    [Fact]
    public async Task Servidor_em_subpasta_resolve_o_caminho_da_api()
    {
        var blob = new byte[] { 9, 9 };
        var (api, h) = Make("https://x.test/rh/api/v1");
        h.Responses.Enqueue(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(blob) });
        await Updater.DownloadAndVerifyAsync(api, new UpdateInfo(true, "1.4.0", "/api/v1/client-updates/windows/download/s.exe", Sha(blob), 2), Temp());
        Assert.Equal("/rh/api/v1/client-updates/windows/download/s.exe", h.Requests[0].Path);
    }

    [Fact]
    public async Task CheckAsync_so_oferece_versao_mais_nova()
    {
        var json = """{"available":true,"version":"1.3.0","url":"/api/v1/client-updates/windows/download/a.exe","sha256":"__SHA__","size":1,"notes":""}""".Replace("__SHA__", new string('c', 64));
        var (api, h) = Make();
        h.Enqueue(HttpStatusCode.OK, json);
        Assert.Null(await Updater.CheckAsync(api, "1.3.0"));
        h.Enqueue(HttpStatusCode.OK, json);
        Assert.Equal("1.3.0", (await Updater.CheckAsync(api, "1.3.0-rc.1"))?.Version);
        h.Enqueue(HttpStatusCode.OK, """{"available":false,"reason":"Nenhuma atualização publicada."}""");
        Assert.Null(await Updater.CheckAsync(api, "1.0.0"));
    }
}

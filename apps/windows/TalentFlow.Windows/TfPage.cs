using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows;

/// <summary>
/// Página que carrega dados do servidor, mostra carregamento/erro/sem permissão e se recarrega sozinha
/// quando OUTRO cliente (site, Android, outro PC) altera as entidades observadas.
/// </summary>
public abstract class TfPage : Page
{
    private readonly StackPanel _body = new();
    private bool _hasContent;

    /// <summary>Entidades cujas mudanças (feed de sync) recarregam esta página.</summary>
    protected abstract string[] Entities { get; }

    /// <summary>Busca os dados e monta a interface. Pode lançar ApiException/NetworkException.</summary>
    protected abstract Task<UIElement> BuildAsync();

    protected TfPage()
    {
        Background = Ui.Brush("canvas");
        Content = new ScrollViewer
        {
            VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
            Content = new Border { Padding = new Thickness(32, 24, 32, 32), Child = _body }
        };
        Loaded += async (_, _) => { AppState.Changed += OnChanged; await ReloadAsync(first: true); };
        Unloaded += (_, _) => AppState.Changed -= OnChanged;
    }

    private void OnChanged(HashSet<string> changed)
    {
        if (Entities.Any(changed.Contains)) _ = ReloadAsync(first: false);
    }

    protected async Task ReloadAsync(bool first = false)
    {
        if (first || !_hasContent) { _body.Children.Clear(); _body.Children.Add(Ui.Loading()); }
        try
        {
            var content = await BuildAsync();
            _body.Children.Clear(); _body.Children.Add(content); _hasContent = true;
        }
        catch (AuthExpiredException) { AppState.ExpireSession(); }
        catch (Exception e) when (e is ApiException or NetworkException)
        {
            if (_hasContent)
            {
                // Mantém o que já estava na tela e avisa que está desatualizado (nunca inventa dados).
                if (_body.Children.Count > 0 && _body.Children[0] is not Microsoft.UI.Xaml.Controls.Border { Tag: "stale" })
                    _body.Children.Insert(0, new Microsoft.UI.Xaml.Controls.Border { Tag = "stale", Child = Ui.Banner("Dados possivelmente desatualizados", e.Message) });
            }
            else { _body.Children.Clear(); _body.Children.Add(Ui.ErrorView(e, () => _ = ReloadAsync(first: true))); }
        }
    }

    /// <summary>Executa uma escrita; em conflito mostra o diálogo e recarrega a versão atual.</summary>
    protected async Task<bool> RunAsync(Func<Task> action, string? okMessage = null)
    {
        var r = await AppState.ActAsync(action);
        if (r.Ok) { await ReloadAsync(); return true; }
        if (r.Conflict) { await Ui.ShowConflict(XamlRoot, r.Message); await ReloadAsync(); }
        else await Ui.ShowDialog(XamlRoot, "Não foi possível concluir", Ui.Text(r.Message), "OK", "Fechar");
        return false;
    }
}

using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

/// <summary>Primeiro uso: endereço do servidor (nenhum domínio é presumido). Depois: login.</summary>
public sealed class ConnectPage : Page
{
    private readonly StackPanel _form = new() { Spacing = 14, MaxWidth = 380 };
    private string? _message;

    public ConnectPage()
    {
        Background = Ui.Brush("canvas");
        var art = new StackPanel { Spacing = 16, VerticalAlignment = VerticalAlignment.Center, Padding = new Thickness(56), Background = Ui.Brush("brandStrong") };
        art.Children.Add(new TextBlock { Text = "TALENTFLOW PEOPLE", FontFamily = Ui.Mono, FontSize = 12, CharacterSpacing = 100, Foreground = Ui.Brush("onBrand") });
        art.Children.Add(new TextBlock { Text = "Pessoas, da vaga à carreira, em um só registro.", FontFamily = Ui.Serif, FontSize = 36, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Foreground = Ui.Brush("onBrand"), TextWrapping = TextWrapping.Wrap, MaxWidth = 460 });
        art.Children.Add(new TextBlock { Text = "Os mesmos dados no site, no Android e no Windows.", Foreground = Ui.Brush("onBrand"), Opacity = 0.85, FontSize = 15 });
        var grid = new Grid { ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1.2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star), MinWidth = 440 } } };
        grid.Children.Add(art);
        var right = new Grid { Padding = new Thickness(40) }; right.Children.Add(new ScrollViewer { VerticalAlignment = VerticalAlignment.Center, Content = _form });
        Grid.SetColumn(right, 1); grid.Children.Add(right);
        Content = grid;
        Loaded += (_, _) => Render();
    }

    protected override void OnNavigatedTo(NavigationEventArgs e) => _message = e.Parameter as string;

    private void Render()
    {
        _form.Children.Clear();
        if (AppState.Api is null || string.IsNullOrEmpty(AppState.ServerBase)) RenderServer(); else RenderLogin();
    }

    private void RenderServer()
    {
        _form.Children.Add(Ui.Serifed("Conectar ao servidor", 26));
        _form.Children.Add(Ui.Text("Informe o endereço do TalentFlow da sua empresa, o mesmo do site (por exemplo rh.suaempresa.com.br).", 14, "inkMuted"));
        var address = new TextBox { Header = "Endereço do servidor", PlaceholderText = "rh.suaempresa.com.br" };
        var error = new StackPanel();
        var go = Ui.PrimaryButton("Continuar", () => { });
        go.HorizontalAlignment = HorizontalAlignment.Stretch;
        async void Submit()
        {
            go.IsEnabled = false; go.Content = "Verificando…"; error.Children.Clear();
            var err = await AppState.SetServerAsync(address.Text);
            go.IsEnabled = true; go.Content = "Continuar";
            if (err is null) Render(); else error.Children.Add(Ui.Banner(err, "", "critical"));
        }
        go.Click += (_, _) => Submit();
        address.KeyDown += (_, k) => { if (k.Key == Windows.System.VirtualKey.Enter) Submit(); };
        _form.Children.Add(address); _form.Children.Add(error); _form.Children.Add(go);
    }

    private void RenderLogin()
    {
        _form.Children.Add(Ui.Serifed("Entrar", 26));
        if (!string.IsNullOrEmpty(_message)) _form.Children.Add(Ui.Banner(_message!, "", "critical"));
        var email = new TextBox { Header = "E-mail" };
        var password = new PasswordBox { Header = "Senha" };
        var error = new StackPanel();
        var go = Ui.PrimaryButton("Entrar", () => { }); go.HorizontalAlignment = HorizontalAlignment.Stretch;
        async void Submit()
        {
            if (string.IsNullOrWhiteSpace(email.Text) || password.Password.Length == 0) return;
            go.IsEnabled = false; go.Content = "Entrando…"; error.Children.Clear();
            var err = await AppState.LoginAsync(email.Text, password.Password);
            go.IsEnabled = true; go.Content = "Entrar";
            if (err is null) App.MainWindow?.ShowShell(); else error.Children.Add(Ui.Banner(err, "", "critical"));
        }
        go.Click += (_, _) => Submit();
        password.KeyDown += (_, k) => { if (k.Key == Windows.System.VirtualKey.Enter) Submit(); };
        var change = new HyperlinkButton { Content = "Alterar servidor" };
        change.Click += async (_, _) => { await AppState.ChangeServerAsync(); _message = null; Render(); };
        _form.Children.Add(email); _form.Children.Add(password); _form.Children.Add(error); _form.Children.Add(go);
        _form.Children.Add(Ui.Text(AppState.ServerBase ?? "", 12, "inkFaint")); _form.Children.Add(change);
    }
}

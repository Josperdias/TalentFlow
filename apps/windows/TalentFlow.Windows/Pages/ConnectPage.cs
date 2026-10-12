using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using TalentFlow.Windows.Services;
using Windows.UI;

namespace TalentFlow.Windows.Pages;

/// <summary>Primeiro uso: endereço do servidor (nenhum domínio é presumido). Depois: login.</summary>
public sealed class ConnectPage : Page
{
    private readonly StackPanel _form = new() { Spacing = 14, MaxWidth = 380 };
    private string? _message;

    public ConnectPage(string? message = null)
    {
        _message = message;
        Background = Ui.Brush("canvas");
        var art = new StackPanel { Spacing = 18, VerticalAlignment = VerticalAlignment.Center, Padding = new Thickness(64) };
        var brand = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 14, Margin = new Thickness(0, 0, 0, 24) };
        brand.Children.Add(Ui.Mark(44));
        brand.Children.Add(new TextBlock { Text = "TalentFlow People", FontFamily = Ui.Serif, FontSize = 24, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White), VerticalAlignment = VerticalAlignment.Center });
        art.Children.Add(brand);
        art.Children.Add(new TextBlock { Text = "RECRUTAMENTO · PESSOAS · DESENVOLVIMENTO", FontFamily = Ui.SansBold, FontSize = 11, CharacterSpacing = 200, Foreground = new SolidColorBrush(Color.FromArgb(255, 0xCF, 0xC6, 0xFF)) });
        art.Children.Add(new TextBlock { Text = "Pessoas, da vaga à carreira, em um só registro.", FontFamily = Ui.Serif, FontSize = 46, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White), TextWrapping = TextWrapping.Wrap, MaxWidth = 520 });
        art.Children.Add(new TextBlock { Text = "Os mesmos dados no site, no Android e no Windows: o que uma pessoa altera aparece para as outras em segundos.", FontSize = 16, MaxWidth = 480, TextWrapping = TextWrapping.Wrap, Foreground = new SolidColorBrush(Color.FromArgb(255, 0xDC, 0xE1, 0xF7)) });
        foreach (var point in new[] { "Sincronização entre todos os aplicativos", "Permissões e dados separados por empresa", "Conflitos de edição nunca sobrescrevem em silêncio" })
        {
            art.Children.Add(new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(28, 255, 255, 255)), BorderBrush = new SolidColorBrush(Color.FromArgb(52, 255, 255, 255)), BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(14), Padding = new Thickness(16, 10, 16, 10), HorizontalAlignment = HorizontalAlignment.Left,
                Child = new TextBlock { Text = point, FontFamily = Ui.SansSemiBold, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, FontSize = 14, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White) }
            }.RiseIn(300 + art.Children.Count * 60));
        }
        var hero = new Grid { Background = Ui.Gradient(Color.FromArgb(255, 0x0B, 0x12, 0x30), Color.FromArgb(255, 0x4A, 0x3B, 0xC8)) };
        hero.Children.Add(art);
        var grid = new Grid { ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1.2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star), MinWidth = 460 } } };
        grid.Children.Add(hero);
        var card = Ui.Panel(_form, new Thickness(36)); card.MaxWidth = 440; card.VerticalAlignment = VerticalAlignment.Center; card.HorizontalAlignment = HorizontalAlignment.Center;
        var right = new Grid { Padding = new Thickness(40) }; right.Children.Add(new ScrollViewer { VerticalAlignment = VerticalAlignment.Center, Content = card.RiseIn(150) });
        Grid.SetColumn(right, 1); grid.Children.Add(right);
        Content = grid;
        Loaded += (_, _) => Render();
    }

    private void Render()
    {
        _form.Children.Clear();
        if (AppState.Api is null || string.IsNullOrEmpty(AppState.ServerBase)) RenderServer(); else RenderLogin();
    }

    private void RenderServer()
    {
        _form.Children.Add(Ui.Serifed("Conectar ao servidor", 30));
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
        address.KeyDown += (_, k) => { if (k.Key == global::Windows.System.VirtualKey.Enter) Submit(); };
        _form.Children.Add(address); _form.Children.Add(error); _form.Children.Add(go);
    }

    private void RenderLogin()
    {
        _form.Children.Add(Ui.Serifed("Entrar", 30));
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
        password.KeyDown += (_, k) => { if (k.Key == global::Windows.System.VirtualKey.Enter) Submit(); };
        var change = new HyperlinkButton { Content = "Alterar servidor" };
        change.Click += async (_, _) => { await AppState.ChangeServerAsync(); _message = null; Render(); };
        _form.Children.Add(email); _form.Children.Add(password); _form.Children.Add(error); _form.Children.Add(go);
        _form.Children.Add(Ui.Text(AppState.ServerBase ?? "", 12, "inkFaint")); _form.Children.Add(change);
    }
}

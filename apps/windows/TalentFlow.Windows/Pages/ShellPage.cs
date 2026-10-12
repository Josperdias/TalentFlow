using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using TalentFlow.Windows.Services;
using Windows.UI;

namespace TalentFlow.Windows.Pages;

/// <summary>Navegação lateral (por papel) + área de conteúdo + estado de sincronização.</summary>
public sealed class ShellPage : Page
{
    private readonly NavigationView _nav = new();
    private readonly ContentControl _content = new() { HorizontalContentAlignment = HorizontalAlignment.Stretch, VerticalContentAlignment = VerticalAlignment.Stretch };

    /// <summary>Shell ativo (para páginas abrirem outras páginas no painel de conteúdo).</summary>
    public static ShellPage? Current { get; private set; }
    private readonly TextBlock _status = new() { FontSize = 12 };
    private readonly Microsoft.UI.Xaml.Shapes.Ellipse _dot = new() { Width = 8, Height = 8, VerticalAlignment = VerticalAlignment.Center };

    public ShellPage()
    {
        Current = this;
        var user = AppState.User!;
        Background = Ui.Brush("canvas");
        _nav.PaneDisplayMode = NavigationViewPaneDisplayMode.Left;
        _nav.IsSettingsVisible = false; _nav.IsBackButtonVisible = NavigationViewBackButtonVisible.Collapsed;
        _nav.OpenPaneLength = 256; _nav.IsPaneToggleButtonVisible = false;
        _nav.Background = Ui.Brush("canvas");

        // Painel lateral navy em gradiente, itens claros e seleção em violeta (tokens nav*).
        var paneBg = Ui.Gradient(Ui.Palette["nav"], Color.FromArgb(255, 0x12, 0x1B, 0x44), vertical: true);
        _nav.Resources["NavigationViewDefaultPaneBackground"] = paneBg;
        _nav.Resources["NavigationViewExpandedPaneBackground"] = paneBg;
        _nav.Resources["NavigationViewItemForeground"] = Ui.Brush("navInk");
        _nav.Resources["NavigationViewItemForegroundPointerOver"] = new SolidColorBrush(Microsoft.UI.Colors.White);
        _nav.Resources["NavigationViewItemForegroundPressed"] = new SolidColorBrush(Microsoft.UI.Colors.White);
        _nav.Resources["NavigationViewItemForegroundSelected"] = Ui.Brush("navActiveInk");
        _nav.Resources["NavigationViewItemForegroundSelectedPointerOver"] = Ui.Brush("navActiveInk");
        _nav.Resources["NavigationViewItemForegroundSelectedPressed"] = Ui.Brush("navActiveInk");
        _nav.Resources["NavigationViewItemBackgroundPointerOver"] = new SolidColorBrush(Color.FromArgb(24, 255, 255, 255));
        _nav.Resources["NavigationViewItemBackgroundPressed"] = new SolidColorBrush(Color.FromArgb(36, 255, 255, 255));
        _nav.Resources["NavigationViewItemBackgroundSelected"] = Ui.Brush("navActive");
        _nav.Resources["NavigationViewItemBackgroundSelectedPointerOver"] = Ui.Brush("navActive");
        _nav.Resources["NavigationViewItemBackgroundSelectedPressed"] = Ui.Brush("navActive");
        _nav.Resources["NavigationViewSelectionIndicatorForeground"] = Ui.Brush("accent");

        var brand = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12, Margin = new Thickness(16, 18, 16, 8) };
        var brandText = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        brandText.Children.Add(new TextBlock { Text = "TalentFlow", FontFamily = Ui.Serif, FontSize = 21, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White) });
        brandText.Children.Add(new TextBlock { Text = "PEOPLE", FontFamily = Ui.SansBold, FontSize = 10, CharacterSpacing = 280, Foreground = Ui.Brush("navMuted") });
        brand.Children.Add(Ui.Mark(38)); brand.Children.Add(brandText);
        _nav.PaneHeader = brand;

        void Add(string text, string tag, Symbol icon) => _nav.MenuItems.Add(new NavigationViewItem { Content = text, Tag = tag, Icon = new SymbolIcon(icon) });
        if (user.Role == "candidate") { Add("Candidaturas", "portal", Symbol.List); }
        else
        {
            Add("Visão geral", "overview", Symbol.Home);
            Add("Vagas", "jobs", Symbol.List);
            Add("Candidatos", "candidates", Symbol.Contact);
            if (user.Role != "interviewer") Add("Pessoas", "people", Symbol.People);
        }
        Add("Conta", "account", Symbol.Account);

        var foot = new StackPanel { Margin = new Thickness(12, 8, 12, 12), Spacing = 10 };
        var pulse = new Button { Padding = new Thickness(12, 6, 12, 6), Background = Ui.Brush("navRaised"), BorderBrush = Ui.Brush("navLine"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(999), HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Left };
        pulse.Resources["ButtonBackgroundPointerOver"] = Ui.Brush("navActive");
        var line = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 }; line.Children.Add(_dot); line.Children.Add(_status);
        pulse.Content = line; pulse.Click += async (_, _) => await AppState.PokeAsync();
        ToolTipService.SetToolTip(pulse, "Verificar agora");
        foot.Children.Add(pulse);
        var card = new Border { Background = Ui.Brush("navRaised"), BorderBrush = Ui.Brush("navLine"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(16), Padding = new Thickness(12) };
        var who = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10 };
        var whoText = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        whoText.Children.Add(new TextBlock { Text = user.Name, FontFamily = Ui.SansBold, FontWeight = Microsoft.UI.Text.FontWeights.Bold, FontSize = 13, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White), TextTrimming = TextTrimming.CharacterEllipsis, MaxWidth = 150 });
        whoText.Children.Add(new TextBlock { Text = $"{Roles.Label(user.Role)} · v{AppState.Version}", FontSize = 12, Foreground = Ui.Brush("navMuted") });
        who.Children.Add(Ui.Avatar(user.Name, 36)); who.Children.Add(whoText);
        card.Child = who; foot.Children.Add(card);
        _nav.PaneFooter = foot;

        _nav.ItemInvoked += (_, e) => { if (e.InvokedItemContainer?.Tag is string tag) Go(tag); };
        _nav.Content = _content;
        Content = _nav;

        Loaded += (_, _) =>
        {
            AppState.ConnectionChanged += OnConnection; OnConnection();
            _nav.SelectedItem = _nav.MenuItems[0]; Go((string)((NavigationViewItem)_nav.MenuItems[0]).Tag);
            AppState.StartSync();
        };
        Unloaded += (_, _) => { AppState.ConnectionChanged -= OnConnection; AppState.Stop(); };
    }

    private void OnConnection()
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            (_status.Text, _dot.Fill) = AppState.Connection switch
            {
                Connection.Online => ("Sincronizado", Ui.Brush("positive")),
                Connection.Offline => ("Sem conexão com o servidor", Ui.Brush("critical")),
                _ => ("Conectando…", Ui.Brush("inkFaint"))
            };
            _status.Foreground = Ui.Brush("navInk");
        });
    }

    private void Go(string tag)
    {
        Show(tag switch
        {
            "overview" => (Page)new OverviewPage(), "jobs" => new JobsPage(), "candidates" => new CandidatesPage(),
            "people" => new PeoplePage(), "portal" => new PortalPage(), _ => new AccountPage()
        });
    }

    /// <summary>Troca a página do painel de conteúdo (sem Frame: as páginas são criadas em código).</summary>
    public void Show(Page page) => _content.Content = page;
}

public static class Roles
{
    public static string Label(string role) => role switch
    {
        "admin" => "Administração", "recruiter" => "Recrutamento", "manager" => "Gestão", "interviewer" => "Entrevistas", "candidate" => "Candidatura", _ => role
    };
}

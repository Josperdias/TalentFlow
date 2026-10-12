using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Windows.Services;

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
        _nav.OpenPaneLength = 232; _nav.IsPaneToggleButtonVisible = false;
        _nav.Background = Ui.Brush("surface");

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

        var foot = new StackPanel { Padding = new Thickness(16, 8, 16, 12), Spacing = 6 };
        var pulse = new Button { Padding = new Thickness(0), Background = Ui.Brush("surface"), BorderThickness = new Thickness(0) };
        var line = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 }; line.Children.Add(_dot); line.Children.Add(_status);
        pulse.Content = line; pulse.Click += async (_, _) => await AppState.PokeAsync();
        ToolTipService.SetToolTip(pulse, "Verificar agora");
        foot.Children.Add(pulse);
        foot.Children.Add(Ui.Text(user.Name, 13, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
        foot.Children.Add(Ui.Text($"{user.Company} · {Roles.Label(user.Role)}", 12, "inkMuted"));
        foot.Children.Add(Ui.Text($"v{AppState.Version}", 11, "inkFaint"));
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
            _status.Foreground = Ui.Brush("inkMuted");
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

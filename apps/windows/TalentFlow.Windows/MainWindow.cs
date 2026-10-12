using Microsoft.UI.Xaml;
using TalentFlow.Windows.Pages;
using TalentFlow.Windows.Services;
using Windows.Graphics;

namespace TalentFlow.Windows;

/// <summary>Janela única: troca entre conexão/login e o shell conforme a sessão.</summary>
public sealed class MainWindow : Window
{
    public MainWindow()
    {
        Title = "TalentFlow People";
        AppWindow.Resize(new SizeInt32(1360, 880));
        var icon = Path.Combine(AppContext.BaseDirectory, "Assets", "talentflow.ico");
        if (File.Exists(icon)) AppWindow.SetIcon(icon);
        AppState.SignedOut += () => DispatcherQueue.TryEnqueue(() => Content = new ConnectPage("Sua sessão foi encerrada. Entre novamente."));
        _ = StartAsync();
    }

    private async Task StartAsync()
    {
        AppState.LoadSettings();
        if (AppState.Api is null) { Content = new ConnectPage(); return; }
        var (user, error) = await AppState.TryRestoreAsync();
        Content = user is not null ? new ShellPage() : new ConnectPage(error);
    }

    public void ShowShell() => Content = new ShellPage();
}

using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Windows.Pages;
using TalentFlow.Windows.Services;
using Windows.Graphics;

namespace TalentFlow.Windows;

/// <summary>Janela única: troca entre conexão/login e o shell conforme a sessão.</summary>
public sealed class MainWindow : Window
{
    private readonly Frame _frame = new();

    public MainWindow()
    {
        Title = "TalentFlow People";
        Content = _frame;
        AppWindow.Resize(new SizeInt32(1360, 880));
        var icon = Path.Combine(AppContext.BaseDirectory, "Assets", "talentflow.ico");
        if (File.Exists(icon)) AppWindow.SetIcon(icon);
        AppState.SignedOut += () => DispatcherQueue.TryEnqueue(() => _frame.Navigate(typeof(ConnectPage), "Sua sessão foi encerrada. Entre novamente."));
        _ = StartAsync();
    }

    private async Task StartAsync()
    {
        AppState.LoadSettings();
        if (AppState.Api is null) { _frame.Navigate(typeof(ConnectPage)); return; }
        var (user, error) = await AppState.TryRestoreAsync();
        if (user is not null) _frame.Navigate(typeof(ShellPage));
        else _frame.Navigate(typeof(ConnectPage), error);
    }

    public void ShowShell() => _frame.Navigate(typeof(ShellPage));
}

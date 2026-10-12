using Microsoft.UI.Xaml;

namespace TalentFlow.Windows;

public partial class App : Application
{
    public static MainWindow? MainWindow { get; private set; }

    public App()
    {
        InitializeComponent();
        UnhandledException += (_, e) =>
        {
            // Nunca derrubar o aplicativo em silêncio: registra e mostra a causa na próxima abertura do diagnóstico.
            Services.Diagnostics.Log("UnhandledException", e.Exception);
            e.Handled = true;
        };
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        Resources["ContentControlThemeFontFamily"] = Ui.Sans;
        MainWindow = new MainWindow();
        MainWindow.Activate();
    }
}

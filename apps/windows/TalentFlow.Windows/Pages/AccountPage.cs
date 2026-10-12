using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

public sealed class AccountPage : TfPage
{
    private string _message = "";
    protected override string[] Entities => [];

    protected override async Task<UIElement> BuildAsync()
    {
        var user = AppState.User!;
        var sessions = await AppState.Api!.SessionsAsync();
        var root = new StackPanel { Spacing = 10 };
        root.Children.Add(Ui.PageHeader("Conta", user.Name, $"{user.Email} · {user.Company} · {Roles.Label(user.Role)}",
            Ui.SecondaryButton("Sair", async () => await AppState.LogoutAsync())));
        if (AppState.UpdateNotice is { } notice) root.Children.Add(Ui.Banner("Atualização necessária", notice));
        if (_message.Length > 0) root.Children.Add(Ui.Banner(_message, "", "info"));

        root.Children.Add(Ui.Eyebrow("Aplicativo"));
        root.Children.Add(Ui.Text($"TalentFlow People {AppState.Version}", 14));
        root.Children.Add(Ui.Text(AppState.ServerBase ?? "", 12, "inkFaint"));
        root.Children.Add(Ui.Text($"Arquivos locais e registro de diagnóstico: {Diagnostics.Folder}", 12, "inkFaint"));
        root.Children.Add(Ui.SecondaryButton("Verificar atualizações", async () =>
        {
            var has = await AppState.CheckUpdateAsync();
            _message = has ? $"Versão {AppState.PendingUpdate!.Version} disponível: use \"Atualizar agora\" na barra no topo." : "Você já está na versão mais recente publicada pelo seu servidor.";
            await ReloadAsync();
        }));

        root.Children.Add(new Border { Height = 8 });
        root.Children.Add(Ui.Eyebrow("Sessões ativas"));
        var rows = new StackPanel();
        foreach (var s in sessions)
        {
            var g = new Grid { Padding = new Thickness(12, 8, 12, 8), ColumnDefinitions = { new ColumnDefinition(), new ColumnDefinition { Width = GridLength.Auto } } };
            g.Children.Add(Ui.Text($"{s.Client} · {(s.Kind == "cookie" ? "navegador" : "aplicativo")}", 14));
            if (s.Current) { var t = Ui.Tag("Esta sessão", "info"); Grid.SetColumn(t, 1); g.Children.Add(t); }
            rows.Children.Add(new Border { BorderBrush = Ui.Brush("line"), BorderThickness = new Thickness(0, 0, 0, 1), Child = g });
        }
        root.Children.Add(Ui.Panel(rows, new Thickness(0)));
        var actions = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Margin = new Thickness(0, 8, 0, 0) };
        actions.Children.Add(Ui.SecondaryButton("Encerrar as outras sessões", async () =>
        {
            var n = await AppState.Api!.RevokeOtherSessionsAsync(); _message = $"{n} outra(s) sessão(ões) encerrada(s)."; await ReloadAsync();
        }));
        actions.Children.Add(Ui.SecondaryButton("Trocar de servidor", async () =>
        {
            await AppState.ChangeServerAsync();
            AppState.ExpireSession();
        }));
        root.Children.Add(actions);
        return root;
    }
}

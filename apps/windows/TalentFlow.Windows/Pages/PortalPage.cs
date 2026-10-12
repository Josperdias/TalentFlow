using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

public sealed class PortalPage : TfPage
{
    protected override string[] Entities => [];

    protected override async Task<UIElement> BuildAsync()
    {
        var portal = await AppState.Api!.PortalAsync();
        var root = new StackPanel { Spacing = 10 };
        root.Children.Add(Ui.PageHeader("Candidatura", "Minhas candidaturas", "Acompanhe em que etapa está cada processo seletivo."));
        if (portal.Applications.Count == 0) { root.Children.Add(Ui.Empty("Nenhuma candidatura encontrada", "Candidaturas feitas com este e-mail aparecem aqui.")); return root; }
        foreach (var a in portal.Applications)
        {
            var s = new StackPanel { Spacing = 4 };
            s.Children.Add(Ui.Text(a.Job, 15, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
            s.Children.Add(Ui.Text(a.Company, 12, "inkMuted"));
            s.Children.Add(Ui.Tag(a.Stage));
            if (a.Interviews.Count > 0) s.Children.Add(Ui.Text("Entrevistas: " + string.Join(", ", a.Interviews.Select(i => i.StartsAt.Length >= 16 ? i.StartsAt[..16].Replace('T', ' ') : i.StartsAt)), 13));
            root.Children.Add(Ui.Panel(s));
        }
        return root;
    }
}

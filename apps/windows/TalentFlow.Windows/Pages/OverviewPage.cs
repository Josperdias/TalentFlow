using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

public sealed class OverviewPage : TfPage
{
    protected override string[] Entities => ["job", "application", "interview", "offer", "task", "employee", "development_plan", "leave_request"];

    protected override async Task<UIElement> BuildAsync()
    {
        var user = AppState.User!;
        var api = AppState.Api!;
        var dash = await api.DashboardAsync();
        var showPeople = user.Role != "interviewer";
        var insights = showPeople ? await api.InsightsAsync() : null;
        var m = dash.Metrics;

        var root = new StackPanel { Spacing = 8 };
        root.Children.Add(Ui.PageHeader(DateTime.Now.ToString("dddd, d 'de' MMMM", new System.Globalization.CultureInfo("pt-BR")),
            $"Olá, {user.Name.Split(' ')[0]}", "Situação atual calculada a partir dos registros do servidor."));
        if (AppState.UpdateNotice is { } notice) root.Children.Add(Ui.Banner("Atualização necessária", notice));

        var left = new StackPanel { Spacing = 8 };
        left.Children.Add(Ui.Eyebrow("Recrutamento"));
        var total = m.CandidatesActive + m.Hired + m.Rejected;
        left.Children.Add(Ui.Ledger(
            Ui.LedgerRow("Vagas abertas", $"{m.JobsApproval} em aprovação", m.JobsOpen.ToString()),
            Ui.LedgerRow("Candidaturas ativas", $"{m.Interviews} entrevista(s) agendada(s)", m.CandidatesActive.ToString()),
            Ui.LedgerRow("Contratações", $"{m.Rejected} reprovação(ões) registradas", m.Hired.ToString()),
            // Sem contratações não há média: "—", nunca um zero enganoso.
            Ui.LedgerRow("Tempo até contratar", m.Hired == 0 ? "Sem contratações para calcular" : "dias, média das contratações", m.Hired == 0 ? "—" : m.AvgTimeHire.ToString("0.0")),
            Ui.LedgerRow("Conversão", "contratados ÷ candidaturas totais", total == 0 ? "—" : $"{m.Conversion:0.0}%", last: true)));
        if (insights is not null)
        {
            left.Children.Add(new Border { Height = 12 });
            left.Children.Add(Ui.Eyebrow("Pessoas"));
            left.Children.Add(Ui.Ledger(
                Ui.LedgerRow("Colaboradores ativos", $"de {insights.Population} registrados", insights.Active.ToString()),
                Ui.LedgerRow("Planos de desenvolvimento concluídos", "Execução de PDI, não evidência de ganho de competência", insights.PlanCount == 0 ? "—" : $"{insights.CompletedPlans}/{insights.PlanCount}"),
                Ui.LedgerRow("Ausências pendentes", "aguardando decisão", insights.PendingLeaves.ToString(), last: true)));
        }

        var right = new StackPanel { Spacing = 6 };
        right.Children.Add(Ui.Eyebrow("Funil de candidaturas por etapa"));
        if (dash.Stages.Count == 0) right.Children.Add(Ui.Text("Sem candidaturas ainda.", 14, "inkMuted"));
        var max = Math.Max(1, dash.Stages.Select(s => s.Value).DefaultIfEmpty(1).Max());
        foreach (var s in dash.Stages)
        {
            var row = new Grid { ColumnSpacing = 10, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(130) }, new ColumnDefinition(), new ColumnDefinition { Width = new GridLength(36) } } };
            row.Children.Add(Ui.Text(s.Name, 13));
            var track = new Grid { Height = 10, Background = Ui.Brush("sunken"), CornerRadius = new CornerRadius(2), VerticalAlignment = VerticalAlignment.Center };
            track.Children.Add(new Border { Background = Ui.Brush("brand"), HorizontalAlignment = HorizontalAlignment.Left, Width = 0, Tag = (double)s.Value / max });
            track.SizeChanged += (_, e) => { if (track.Children[0] is Border b && b.Tag is double f) b.Width = Math.Max(2, e.NewSize.Width * f); };
            Grid.SetColumn(track, 1); row.Children.Add(track);
            var n = Ui.Text(s.Value.ToString(), 13); n.TextAlignment = TextAlignment.Right; Grid.SetColumn(n, 2); row.Children.Add(n);
            right.Children.Add(row);
        }

        var cols = new Grid { ColumnSpacing = 40, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(3, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) } } };
        cols.Children.Add(left); Grid.SetColumn(right, 1); cols.Children.Add(right);
        root.Children.Add(cols);
        return root;
    }
}

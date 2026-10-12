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

        var root = new StackPanel { Spacing = 10 };
        root.Children.Add(Ui.PageHeader(DateTime.Now.ToString("dddd, d 'de' MMMM", new System.Globalization.CultureInfo("pt-BR")),
            $"Olá, {user.Name.Split(' ')[0]}", "Situação atual calculada a partir dos registros do servidor."));
        if (AppState.UpdateNotice is { } notice) root.Children.Add(Ui.Banner("Atualização necessária", notice));

        var total = m.CandidatesActive + m.Hired + m.Rejected;
        root.Children.Add(Ui.Eyebrow("Recrutamento"));
        root.Children.Add(Ui.KpiGrid(3,
            Ui.Kpi("Vagas abertas", m.JobsOpen.ToString(), $"{m.JobsApproval} em aprovação", "brand", 0),
            Ui.Kpi("Candidaturas ativas", m.CandidatesActive.ToString(), $"{m.Interviews} entrevista(s) agendada(s)", "info", 60),
            Ui.Kpi("Contratações", m.Hired.ToString(), $"{m.Rejected} reprovação(ões) registradas", "positive", 120),
            // Sem contratações não há média: "—", nunca um zero enganoso.
            Ui.Kpi("Tempo até contratar", m.Hired == 0 ? "—" : m.AvgTimeHire.ToString("0.0"), m.Hired == 0 ? "Sem contratações para calcular" : "dias, média das contratações", "attention", 180),
            Ui.Kpi("Conversão", total == 0 ? "—" : $"{m.Conversion:0.0}%", "contratados ÷ candidaturas totais", "brand", 240)));
        if (insights is not null)
        {
            root.Children.Add(new Border { Height = 8 });
            root.Children.Add(Ui.Eyebrow("Pessoas"));
            root.Children.Add(Ui.KpiGrid(3,
                Ui.Kpi("Colaboradores ativos", insights.Active.ToString(), $"de {insights.Population} registrados", "brand", 0),
                Ui.Kpi("Planos de desenvolvimento concluídos", insights.PlanCount == 0 ? "—" : $"{insights.CompletedPlans}/{insights.PlanCount}", "Execução de PDI, não evidência de ganho de competência", "positive", 60),
                Ui.Kpi("Ausências pendentes", insights.PendingLeaves.ToString(), "aguardando decisão", "attention", 120)));
        }

        var funnel = new StackPanel { Spacing = 12 };
        funnel.Children.Add(Ui.Text("Funil de candidaturas por etapa", 15, "ink", Microsoft.UI.Text.FontWeights.Bold));
        if (dash.Stages.Count == 0) funnel.Children.Add(Ui.Text("Sem candidaturas ainda.", 14, "inkMuted"));
        var max = Math.Max(1, dash.Stages.Select(s => s.Value).DefaultIfEmpty(1).Max());
        var n = 0;
        foreach (var s in dash.Stages)
        {
            var row = new Grid { ColumnSpacing = 12, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(130) }, new ColumnDefinition(), new ColumnDefinition { Width = new GridLength(36) } } };
            row.Children.Add(Ui.Text(s.Name, 13, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
            var track = Ui.GrowBar((double)s.Value / max, n++ * 70);
            Grid.SetColumn(track, 1); row.Children.Add(track);
            var num = Ui.Text(s.Value.ToString(), 13, "ink", Microsoft.UI.Text.FontWeights.Bold); num.TextAlignment = TextAlignment.Right; Grid.SetColumn(num, 2); row.Children.Add(num);
            funnel.Children.Add(row);
        }

        var slices = new List<(string Label, int Value, global::Windows.UI.Color Color)>
        {
            ("Ativas", m.CandidatesActive, Ui.Palette["brand"]),
            ("Contratadas", m.Hired, global::Windows.UI.Color.FromArgb(255, 0x12, 0x90, 0x6A)),
            ("Reprovadas", m.Rejected, global::Windows.UI.Color.FromArgb(255, 0xC0, 0x50, 0x6A)),
        };
        var legend = new StackPanel { Spacing = 10, VerticalAlignment = VerticalAlignment.Center };
        foreach (var sl in slices)
        {
            var line = new Grid { ColumnSpacing = 10, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(12) }, new ColumnDefinition(), new ColumnDefinition { Width = GridLength.Auto } } };
            line.Children.Add(new Border { Width = 12, Height = 12, CornerRadius = new CornerRadius(4), Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(sl.Color), VerticalAlignment = VerticalAlignment.Center });
            var name = Ui.Text(sl.Label, 13, "ink", Microsoft.UI.Text.FontWeights.SemiBold); Grid.SetColumn(name, 1); line.Children.Add(name);
            var value = Ui.Text(sl.Value.ToString(), 13, "ink", Microsoft.UI.Text.FontWeights.Bold); Grid.SetColumn(value, 2); line.Children.Add(value);
            legend.Children.Add(line);
        }
        var donutRow = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 24 };
        donutRow.Children.Add(Ui.Donut(slices, "candidaturas")); donutRow.Children.Add(legend);
        var status = new StackPanel { Spacing = 16 };
        status.Children.Add(Ui.Text("Situação das candidaturas", 15, "ink", Microsoft.UI.Text.FontWeights.Bold)); status.Children.Add(donutRow);

        var cols = new Grid { ColumnSpacing = 20, Margin = new Thickness(0, 20, 0, 0), ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(3, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) } } };
        var funnelPanel = Ui.Panel(funnel, new Thickness(22)).RiseIn(260);
        var statusPanel = Ui.Panel(status, new Thickness(22)).RiseIn(320); statusPanel.VerticalAlignment = VerticalAlignment.Top;
        cols.Children.Add(funnelPanel); Grid.SetColumn(statusPanel, 1); cols.Children.Add(statusPanel);
        root.Children.Add(cols);
        return root;
    }
}

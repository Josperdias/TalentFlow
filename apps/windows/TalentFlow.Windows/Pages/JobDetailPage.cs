using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

/// <summary>Pipeline da vaga. Mover candidatura e editar usam If-Match: conflito vira diálogo, nunca sobrescreve.</summary>
public sealed class JobDetailPage : TfPage
{
    private readonly int _jobId;
    private Job? _opened;            // versão em que a edição foi aberta (presa à versão vista)
    protected override string[] Entities => ["job", "application", "job_stage", "interview", "scorecard"];

    public JobDetailPage(int jobId) { _jobId = jobId; }

    protected override async Task<UIElement> BuildAsync()
    {
        var user = AppState.User!;
        var canEdit = user.Role is "admin" or "recruiter";
        var canMove = canEdit || user.Role == "manager";
        var detail = await AppState.Api!.JobDetailAsync(_jobId);
        var job = detail.Job; var (label, tone) = JobsPage.Status(job.Status);

        var root = new StackPanel { Spacing = 8 };
        var back = new HyperlinkButton { Content = "‹ Vagas", Padding = new Thickness(0) };
        back.Click += (_, _) => ShellPage.Current?.Show(new JobsPage());
        root.Children.Add(back);
        var actions = new List<UIElement> { Ui.Tag(label, tone) };
        if (canEdit) actions.Add(Ui.SecondaryButton("Editar título", async () => await EditAsync(job)));
        root.Children.Add(Ui.PageHeader(job.Code, job.Title, $"{job.Department} · {job.Location} · versão {job.Version}", actions.ToArray()));

        if (detail.Applications.Count == 0) { root.Children.Add(Ui.Empty("Nenhuma candidatura nesta vaga")); return root; }

        var board = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12 };
        foreach (var stage in detail.Stages)
        {
            var apps = detail.Applications.Where(a => a.StageId == stage.Id).ToList();
            var col = new StackPanel { Spacing = 8, Width = 250, Padding = new Thickness(8), Background = Ui.Brush("sunken") };
            var head = new Grid { ColumnDefinitions = { new ColumnDefinition(), new ColumnDefinition { Width = GridLength.Auto } } };
            head.Children.Add(Ui.Text(stage.Name, 14, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
            var count = Ui.Text(apps.Count.ToString(), 13, "inkMuted"); Grid.SetColumn(count, 1); head.Children.Add(count);
            col.Children.Add(head);
            foreach (var a in apps) col.Children.Add(Card(a, detail.Stages, canMove));
            board.Children.Add(new Border { BorderBrush = Ui.Brush("line"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(4), Child = col });
        }
        root.Children.Add(new ScrollViewer { HorizontalScrollBarVisibility = ScrollBarVisibility.Auto, VerticalScrollBarVisibility = ScrollBarVisibility.Disabled, HorizontalScrollMode = ScrollMode.Enabled, Content = board });
        return root;
    }

    private UIElement Card(ApplicationRow a, List<Stage> stages, bool canMove)
    {
        var s = new StackPanel { Spacing = 4 };
        s.Children.Add(Ui.Text(a.Candidate.Name, 14, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
        s.Children.Add(Ui.Text(string.IsNullOrWhiteSpace(a.Candidate.Title) ? a.Candidate.Location : a.Candidate.Title, 12, "inkMuted"));
        s.Children.Add(Ui.Tag($"Fit {(a.Fit >= 75 ? "alto" : a.Fit >= 50 ? "médio" : "baixo")} · {a.Fit}", a.Fit >= 75 ? "positive" : a.Fit >= 50 ? "info" : "neutral"));
        if (canMove)
        {
            var options = stages.Where(x => x.Id != a.StageId).ToList();
            var combo = new ComboBox { PlaceholderText = "Mover para…", HorizontalAlignment = HorizontalAlignment.Stretch, ItemsSource = options.Select(x => x.Name).ToList() };
            combo.SelectionChanged += async (_, _) =>
            {
                if (combo.SelectedIndex < 0 || combo.SelectedIndex >= options.Count) return;
                var target = options[combo.SelectedIndex];
                var reason = "";
                if (target.Kind != "active")
                {
                    var box = new TextBox { Header = $"Motivo para {a.Candidate.Name}", AcceptsReturn = true, MinHeight = 80, MinWidth = 340 };
                    var panel = new StackPanel { Spacing = 8 }; panel.Children.Add(Ui.Text("Decisões finais exigem um motivo, que fica no histórico e na auditoria.", 13, "inkMuted")); panel.Children.Add(box);
                    if (await Ui.ShowDialog(XamlRoot, target.Kind == "hired" ? "Registrar contratação" : "Registrar reprovação", panel, "Confirmar") != ContentDialogResult.Primary) { combo.SelectedIndex = -1; return; }
                    reason = box.Text.Trim();
                    if (reason.Length < 3) { await Ui.ShowDialog(XamlRoot, "Motivo obrigatório", Ui.Text("Informe ao menos 3 caracteres."), "OK", "Fechar"); combo.SelectedIndex = -1; return; }
                }
                await RunAsync(() => AppState.Api!.MoveApplicationAsync(a, target.Id, reason));
            };
            s.Children.Add(combo);
        }
        return new Border { Background = Ui.Brush("surface"), BorderBrush = Ui.Brush("line"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(4), Padding = new Thickness(10), Child = s };
    }

    private async Task EditAsync(Job current)
    {
        _opened = current; // a edição fica presa a ESTA versão: se outra pessoa salvar antes, o servidor responde 409
        var title = Ui.Input("Título", current.Title);
        var panel = new StackPanel { Spacing = 8 }; panel.Children.Add(title);
        if (await Ui.ShowDialog(XamlRoot, "Editar vaga", panel, "Salvar") != ContentDialogResult.Primary) return;
        if (title.Text.Trim().Length < 3) return;
        await RunAsync(() => AppState.Api!.UpdateJobTitleAsync(_opened!, title.Text.Trim()));
    }
}

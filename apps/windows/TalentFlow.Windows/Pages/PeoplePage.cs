using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

/// <summary>Colaboradores, planos de desenvolvimento (PDI) e ausências, em abas.</summary>
public sealed class PeoplePage : TfPage
{
    private int _tab;
    protected override string[] Entities => ["employee", "application", "development_plan", "leave_request"];

    protected override async Task<UIElement> BuildAsync()
    {
        var api = AppState.Api!;
        var user = AppState.User!;
        var employees = await api.EmployeesAsync();
        var plans = await api.PlansAsync();
        var leaves = await api.LeavesAsync();

        var root = new StackPanel { Spacing = 8 };
        root.Children.Add(Ui.PageHeader("Pessoas", "Colaboradores e desenvolvimento", "Gestores veem apenas a própria equipe. Servidor aplica as permissões."));
        var pivot = new Pivot { SelectedIndex = _tab };
        pivot.SelectionChanged += (_, _) => _tab = pivot.SelectedIndex;
        pivot.Items.Add(new PivotItem { Header = "Colaboradores", Content = Employees(employees) });
        pivot.Items.Add(new PivotItem { Header = "Desenvolvimento", Content = Plans(plans) });
        pivot.Items.Add(new PivotItem { Header = "Ausências", Content = Leaves(leaves, user.Role is "admin" or "manager") });
        root.Children.Add(pivot);
        return root;
    }

    private static UIElement Employees(List<Employee> list)
    {
        if (list.Count == 0) return Ui.Empty("Nenhum colaborador encontrado");
        var rows = new StackPanel();
        foreach (var e in list)
        {
            var g = new Grid { Padding = new Thickness(12, 8, 12, 8), ColumnSpacing = 12, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(90) }, new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(100) } } };
            var code = Ui.Text(e.EmployeeCode, 12, "inkMuted"); code.FontFamily = Ui.Mono; g.Children.Add(code);
            var name = Ui.Text(e.Name, 14, "ink", Microsoft.UI.Text.FontWeights.Medium); Grid.SetColumn(name, 1); g.Children.Add(name);
            var job = Ui.Text(string.IsNullOrWhiteSpace(e.JobTitle) ? "—" : e.JobTitle, 13, "inkMuted"); Grid.SetColumn(job, 2); g.Children.Add(job);
            var dep = Ui.Text(e.Department, 13, "inkMuted"); Grid.SetColumn(dep, 3); g.Children.Add(dep);
            var tag = Ui.Tag(e.Status == "active" ? "Ativo" : "Desligado", e.Status == "active" ? "positive" : "neutral"); Grid.SetColumn(tag, 4); g.Children.Add(tag);
            rows.Children.Add(new Border { BorderBrush = Ui.Brush("line"), BorderThickness = new Thickness(0, 0, 0, 1), Child = g });
        }
        return new ScrollViewer { MaxHeight = 560, Content = Ui.Panel(rows, new Thickness(0)) };
    }

    private UIElement Plans(List<Plan> plans)
    {
        var stack = new StackPanel { Spacing = 10, Margin = new Thickness(0, 8, 0, 0) };
        stack.Children.Add(Ui.Text("O progresso mede execução das atividades, não ganho de competência.", 13, "inkMuted"));
        if (plans.Count == 0) { stack.Children.Add(Ui.Empty("Nenhum plano de desenvolvimento")); return stack; }
        foreach (var p in plans)
        {
            var card = new StackPanel { Spacing = 6 };
            var head = new Grid { ColumnDefinitions = { new ColumnDefinition(), new ColumnDefinition { Width = GridLength.Auto } } };
            head.Children.Add(Ui.Text(p.Title, 15, "ink", Microsoft.UI.Text.FontWeights.SemiBold));
            var tag = Ui.Tag(p.Status == "completed" ? "Concluído" : "Em andamento", p.Status == "completed" ? "positive" : "info"); Grid.SetColumn(tag, 1); head.Children.Add(tag);
            card.Children.Add(head);
            card.Children.Add(Ui.Text($"{p.Employee} · prazo {p.DueDate}", 12, "inkMuted"));
            card.Children.Add(new ProgressBar { Value = p.Progress, Maximum = 100, Foreground = Ui.Brush("brand") });
            for (var i = 0; i < p.Actions.Count; i++)
            {
                var index = i; var a = p.Actions[i];
                var cb = new CheckBox { IsChecked = a.Done, IsEnabled = p.Status != "archived", Content = a.Title + (string.IsNullOrWhiteSpace(a.Evidence) ? "" : " — " + a.Evidence) };
                cb.Click += async (_, _) =>
                {
                    var done = cb.IsChecked == true; var evidence = "";
                    if (done)
                    {
                        var box = new TextBox { Header = "Evidência (opcional)", AcceptsReturn = true, MinHeight = 80, MinWidth = 340, MaxLength = 1000 };
                        var panel = new StackPanel { Spacing = 8 }; panel.Children.Add(Ui.Text(a.Title)); panel.Children.Add(box);
                        if (await Ui.ShowDialog(XamlRoot, "Concluir atividade", panel, "Marcar como concluída") != ContentDialogResult.Primary) { cb.IsChecked = false; return; }
                        evidence = box.Text.Trim();
                    }
                    await RunAsync(() => AppState.Api!.SetPlanActionAsync(p, index, done, evidence));
                };
                card.Children.Add(cb);
            }
            stack.Children.Add(Ui.Panel(card));
        }
        return new ScrollViewer { MaxHeight = 560, Content = stack };
    }

    private UIElement Leaves(List<Leave> leaves, bool canDecide)
    {
        var stack = new StackPanel { Spacing = 8, Margin = new Thickness(0, 8, 0, 0) };
        if (leaves.Count == 0) { stack.Children.Add(Ui.Empty("Nenhuma solicitação")); return stack; }
        var kinds = new Dictionary<string, string> { ["vacation"] = "Férias", ["personal"] = "Pessoal", ["medical"] = "Saúde", ["other"] = "Outro" };
        foreach (var l in leaves)
        {
            var g = new Grid { ColumnSpacing = 12, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }, new ColumnDefinition { Width = GridLength.Auto }, new ColumnDefinition { Width = GridLength.Auto } } };
            var left = new StackPanel { Spacing = 2 };
            left.Children.Add(Ui.Text(l.Employee, 14, "ink", Microsoft.UI.Text.FontWeights.Medium));
            left.Children.Add(Ui.Text($"{(kinds.TryGetValue(l.Kind, out var k) ? k : l.Kind)} · {l.StartsOn} a {l.EndsOn} · {l.Days} dia(s)", 12, "inkMuted"));
            g.Children.Add(left);
            var (txt, tone) = l.Status switch { "approved" => ("Aprovada", "positive"), "rejected" => ("Recusada", "critical"), _ => ("Pendente", "attention") };
            var tag = Ui.Tag(txt, tone); Grid.SetColumn(tag, 1); g.Children.Add(tag);
            if (l.Status == "pending" && canDecide)
            {
                var btns = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };
                btns.Children.Add(Ui.SecondaryButton("Recusar", async () => await RunAsync(() => AppState.Api!.DecideLeaveAsync(l.Id, false))));
                btns.Children.Add(Ui.PrimaryButton("Aprovar", async () => await RunAsync(() => AppState.Api!.DecideLeaveAsync(l.Id, true))));
                Grid.SetColumn(btns, 2); g.Children.Add(btns);
            }
            stack.Children.Add(Ui.Panel(g, new Thickness(12)));
        }
        return new ScrollViewer { MaxHeight = 560, Content = stack };
    }
}

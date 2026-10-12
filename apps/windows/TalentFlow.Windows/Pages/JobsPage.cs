using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

public sealed class JobsPage : TfPage
{
    private string _query = "";
    protected override string[] Entities => ["job", "application"];

    internal static (string Label, string Tone) Status(string s) => s switch
    {
        "open" => ("Aberta", "positive"), "approval" => ("Em aprovação", "attention"), "closed" => ("Encerrada", "neutral"), _ => ("Arquivada", "neutral")
    };

    protected override async Task<UIElement> BuildAsync()
    {
        var user = AppState.User!;
        var canEdit = user.Role is "admin" or "recruiter";
        var jobs = await AppState.Api!.JobsAsync();
        var shown = jobs.Where(j => j.Title.Contains(_query, StringComparison.OrdinalIgnoreCase)).ToList();

        var root = new StackPanel { Spacing = 8 };
        UIElement[] actions = canEdit ? [Ui.PrimaryButton("Nova vaga", async () => await NewJobAsync())] : [];
        root.Children.Add(Ui.PageHeader("Recrutamento", "Vagas", "Requisições e vagas com seus pipelines.", actions));

        var search = new TextBox { Header = "Buscar por título", Text = _query, Width = 320, HorizontalAlignment = HorizontalAlignment.Left };
        search.KeyDown += async (_, k) => { if (k.Key == Windows.System.VirtualKey.Enter) { _query = search.Text; await ReloadAsync(); } };
        root.Children.Add(search);

        if (shown.Count == 0) { root.Children.Add(Ui.Empty("Nenhuma vaga encontrada", canEdit ? "Crie a primeira vaga para iniciar um processo seletivo." : "Não há vagas atribuídas a você.")); return root; }

        var grid = new StackPanel();
        grid.Children.Add(Header("Código", "Vaga", "Área", "Local", "Situação", "Candidaturas"));
        foreach (var j in shown)
        {
            var (label, tone) = Status(j.Status);
            var row = Row();
            var code = Ui.Text(j.Code, 12, "inkMuted"); code.FontFamily = Ui.Mono;
            var open = new HyperlinkButton { Content = j.Title, Padding = new Thickness(0), FontWeight = Microsoft.UI.Text.FontWeights.Medium };
            var id = j.Id; open.Click += (_, _) => Frame.Navigate(typeof(JobDetailPage), id);
            Put(row, 0, code); Put(row, 1, open); Put(row, 2, Ui.Text(j.Department, 13)); Put(row, 3, Ui.Text($"{j.Location} · {j.Modality}", 13));
            Put(row, 4, Ui.Tag(label, tone)); var n = Ui.Text(j.Applications.ToString(), 13); n.TextAlignment = TextAlignment.Right; Put(row, 5, n);
            grid.Children.Add(row);
        }
        root.Children.Add(Ui.Panel(grid, new Thickness(0)));
        return root;
    }

    private static Grid Row() => new()
    {
        Padding = new Thickness(12, 0, 12, 0), MinHeight = 36, ColumnSpacing = 12,
        ColumnDefinitions =
        {
            new ColumnDefinition { Width = new GridLength(90) }, new ColumnDefinition { Width = new GridLength(3, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(1.2, GridUnitType.Star) },
            new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(130) }, new ColumnDefinition { Width = new GridLength(100) }
        }
    };

    private static void Put(Grid g, int col, UIElement e) { e.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); Grid.SetColumn((FrameworkElement)e, col); g.Children.Add(e); }

    private static UIElement Header(params string[] names)
    {
        var row = Row(); row.Background = Ui.Brush("sunken"); row.MinHeight = 34;
        for (var i = 0; i < names.Length; i++) { var t = Ui.Text(names[i], 12, "inkMuted", Microsoft.UI.Text.FontWeights.Medium); if (i == 5) t.TextAlignment = TextAlignment.Right; Put(row, i, t); }
        return row;
    }

    private async Task NewJobAsync()
    {
        var title = Ui.Input("Título da vaga"); var dept = Ui.Input("Área"); var place = Ui.Input("Local");
        var status = new ComboBox { Header = "Início como", ItemsSource = new[] { "Em aprovação", "Aberta" }, SelectedIndex = 0, MinWidth = 320 };
        var panel = new StackPanel { Spacing = 10 }; foreach (var c in new UIElement[] { title, dept, place, status }) panel.Children.Add(c);
        if (await Ui.ShowDialog(XamlRoot, "Nova vaga", panel, "Criar vaga") != ContentDialogResult.Primary) return;
        if (title.Text.Trim().Length < 3) { await Ui.ShowDialog(XamlRoot, "Título obrigatório", Ui.Text("Informe um título com ao menos 3 caracteres."), "OK", "Fechar"); return; }
        var st = status.SelectedIndex == 1 ? "open" : "approval";
        if (await RunAsync(() => AppState.Api!.CreateJobAsync(title.Text.Trim(), dept.Text.Trim(), place.Text.Trim(), st))) { }
    }
}

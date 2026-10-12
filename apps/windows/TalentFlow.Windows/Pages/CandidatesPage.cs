using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using TalentFlow.Core;
using TalentFlow.Windows.Services;

namespace TalentFlow.Windows.Pages;

public sealed class CandidatesPage : TfPage
{
    private string _query = "";
    protected override string[] Entities => ["candidate", "application"];

    protected override async Task<UIElement> BuildAsync()
    {
        var list = await AppState.Api!.CandidatesAsync(_query);
        var root = new StackPanel { Spacing = 8 };
        root.Children.Add(Ui.PageHeader("Recrutamento", "Candidatos", "Você só vê pessoas ligadas às vagas que pode acessar."));
        var search = new TextBox { Header = "Buscar por nome, cargo ou habilidade (Enter)", Text = _query, Width = 360, HorizontalAlignment = HorizontalAlignment.Left };
        search.KeyDown += async (_, k) => { if (k.Key == global::Windows.System.VirtualKey.Enter) { _query = search.Text; await ReloadAsync(); } };
        root.Children.Add(search);
        if (list.Count == 0) { root.Children.Add(Ui.Empty("Nenhum candidato encontrado")); return root; }
        var rows = new StackPanel();
        foreach (var c in list)
        {
            var g = new Grid { Padding = new Thickness(12, 8, 12, 8), ColumnSpacing = 12, ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(1.5, GridUnitType.Star) }, new ColumnDefinition { Width = new GridLength(110) } } };
            g.Children.Add(Ui.Text(c.Name, 14, "ink", Microsoft.UI.Text.FontWeights.Medium));
            var t = Ui.Text(string.IsNullOrWhiteSpace(c.Title) ? "—" : c.Title, 13, "inkMuted"); Grid.SetColumn(t, 1); g.Children.Add(t);
            var l = Ui.Text(string.IsNullOrWhiteSpace(c.Location) ? "—" : c.Location, 13, "inkMuted"); Grid.SetColumn(l, 2); g.Children.Add(l);
            var y = Ui.Text($"{c.ExperienceYears} ano(s)", 13, "inkMuted"); y.TextAlignment = TextAlignment.Right; Grid.SetColumn(y, 3); g.Children.Add(y);
            rows.Children.Add(new Border { BorderBrush = Ui.Brush("line"), BorderThickness = new Thickness(0, 0, 0, 1), Child = g });
        }
        root.Children.Add(Ui.Panel(rows, new Thickness(0)));
        return root;
    }
}

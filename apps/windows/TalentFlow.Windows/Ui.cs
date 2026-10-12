using Microsoft.UI;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using TalentFlow.Core;
using TalentFlow.Windows.Styles;
using Windows.UI;

namespace TalentFlow.Windows;

/// <summary>Blocos de interface do design system "Ofício" (mesmos tokens do site e do Android).</summary>
public static class Ui
{
    public static IReadOnlyDictionary<string, Color> Palette =>
        Application.Current.RequestedTheme == ApplicationTheme.Dark ? TfTokens.Dark : TfTokens.Light;

    public static SolidColorBrush Brush(string key) => new(Palette[key]);
    public static readonly FontFamily Serif = new("Georgia");
    public static readonly FontFamily Mono = new("Cascadia Mono, Consolas");

    public static TextBlock Text(string text, double size = 14, string color = "ink", global::Windows.UI.Text.FontWeight? weight = null, bool wrap = true) =>
        new() { Text = text, FontSize = size, Foreground = Brush(color), FontWeight = weight ?? FontWeights.Normal, TextWrapping = wrap ? TextWrapping.Wrap : TextWrapping.NoWrap };

    public static TextBlock Eyebrow(string text) =>
        new() { Text = text.ToUpperInvariant(), FontFamily = Mono, FontSize = 11, CharacterSpacing = 80, Foreground = Brush("inkFaint") };

    public static TextBlock Serifed(string text, double size, string color = "ink") =>
        new() { Text = text, FontFamily = Serif, FontSize = size, FontWeight = FontWeights.SemiBold, Foreground = Brush(color), TextWrapping = TextWrapping.Wrap };

    public static Border Panel(UIElement child, Thickness? padding = null) => new()
    {
        Background = Brush("surface"), BorderBrush = Brush("line"), BorderThickness = new Thickness(1),
        CornerRadius = new CornerRadius(TfTokens.RadiusMd), Padding = padding ?? new Thickness(16), Child = child
    };

    public static Border Tag(string text, string tone = "neutral")
    {
        var (fg, bg) = tone switch
        {
            "positive" => ("positive", "positiveSoft"), "attention" => ("attention", "attentionSoft"),
            "critical" => ("critical", "criticalSoft"), "info" => ("info", "infoSoft"), _ => ("inkMuted", "sunken")
        };
        return new Border
        {
            Background = Brush(bg), BorderBrush = Brush(fg), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(TfTokens.RadiusSm),
            Padding = new Thickness(7, 1, 7, 1), HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Center,
            Child = new TextBlock { Text = text, FontSize = 12, FontWeight = FontWeights.Medium, Foreground = Brush(fg) }
        };
    }

    public static Border Banner(string title, string text = "", string tone = "attention")
    {
        var fg = tone switch { "critical" => "critical", "info" => "info", _ => "attention" };
        var bg = tone switch { "critical" => "criticalSoft", "info" => "infoSoft", _ => "attentionSoft" };
        var stack = new StackPanel { Spacing = 2 };
        stack.Children.Add(Text(title, 14, "ink", FontWeights.SemiBold));
        if (text.Length > 0) stack.Children.Add(Text(text, 13, "ink"));
        return new Border
        {
            Background = Brush(bg), BorderBrush = Brush(fg), BorderThickness = new Thickness(4, 1, 1, 1), CornerRadius = new CornerRadius(TfTokens.RadiusMd),
            Padding = new Thickness(14, 10, 14, 10), Margin = new Thickness(0, 0, 0, 12), Child = stack
        };
    }

    public static Button PrimaryButton(string text, Action onClick)
    {
        var b = new Button { Content = text, Background = Brush("brand"), Foreground = Brush("onBrand"), BorderBrush = Brush("brand"), CornerRadius = new CornerRadius(TfTokens.RadiusMd), Padding = new Thickness(16, 6, 16, 6) };
        b.Resources["ButtonBackgroundPointerOver"] = Brush("brandStrong");
        b.Resources["ButtonForegroundPointerOver"] = Brush("onBrand");
        b.Resources["ButtonBorderBrushPointerOver"] = Brush("brandStrong");
        b.Click += (_, _) => onClick();
        return b;
    }

    public static Button SecondaryButton(string text, Action onClick)
    {
        var b = new Button { Content = text, Background = Brush("surface"), Foreground = Brush("ink"), BorderBrush = Brush("lineStrong"), CornerRadius = new CornerRadius(TfTokens.RadiusMd), Padding = new Thickness(16, 6, 16, 6) };
        b.Click += (_, _) => onClick();
        return b;
    }

    public static StackPanel PageHeader(string eyebrow, string title, string? lead = null, params UIElement[] actions)
    {
        var text = new StackPanel { Spacing = 4 };
        text.Children.Add(Eyebrow(eyebrow)); text.Children.Add(Serifed(title, 28));
        if (!string.IsNullOrEmpty(lead)) text.Children.Add(Text(lead, 14, "inkMuted"));
        var row = new Grid { ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }, new ColumnDefinition { Width = GridLength.Auto } } };
        row.Children.Add(text);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, VerticalAlignment = VerticalAlignment.Bottom };
        foreach (var a in actions) buttons.Children.Add(a);
        Grid.SetColumn(buttons, 1); row.Children.Add(buttons);
        var outer = new StackPanel { Spacing = 12, Margin = new Thickness(0, 0, 0, 16) };
        outer.Children.Add(row);
        outer.Children.Add(new Border { Height = 1, Background = Brush("line") });
        return outer;
    }

    public static UIElement Loading() => new StackPanel { Padding = new Thickness(0, 40, 0, 0), HorizontalAlignment = HorizontalAlignment.Center, Children = { new ProgressRing { IsActive = true, Width = 36, Height = 36 } } };

    public static UIElement Empty(string title, string text = "")
    {
        var s = new StackPanel { Spacing = 4, HorizontalAlignment = HorizontalAlignment.Center };
        s.Children.Add(Text(title, 15, "ink", FontWeights.SemiBold));
        if (text.Length > 0) s.Children.Add(Text(text, 13, "inkMuted"));
        return new Border { BorderBrush = Brush("lineStrong"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(TfTokens.RadiusMd), Padding = new Thickness(32), Child = s };
    }

    public static UIElement ErrorView(Exception e, Action retry)
    {
        var forbidden = e is ApiException { IsForbidden: true };
        var title = e is NetworkException ? "Sem conexão com o servidor" : forbidden ? "Sem permissão para ver esta área" : "Não foi possível carregar";
        var panel = new StackPanel();
        panel.Children.Add(Banner(title, e.Message, forbidden ? "attention" : "critical"));
        if (!forbidden) panel.Children.Add(SecondaryButton("Tentar novamente", retry));
        return panel;
    }

    /// <summary>Linha de livro-razão: rótulo e nota à esquerda, número em serifa à direita.</summary>
    public static UIElement LedgerRow(string label, string note, string figure, bool last = false)
    {
        var left = new StackPanel { Spacing = 1 };
        left.Children.Add(Text(label, 14)); left.Children.Add(Text(note, 12, "inkMuted"));
        var g = new Grid { Padding = new Thickness(16, 10, 16, 10), ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }, new ColumnDefinition { Width = GridLength.Auto } } };
        g.Children.Add(left);
        var fig = Serifed(figure, 22); fig.VerticalAlignment = VerticalAlignment.Center; fig.TextAlignment = TextAlignment.Right; Grid.SetColumn(fig, 1); g.Children.Add(fig);
        return new Border { BorderBrush = Brush("line"), BorderThickness = new Thickness(0, 0, 0, last ? 0 : 1), Child = g };
    }

    public static Border Ledger(params UIElement[] rows)
    {
        var s = new StackPanel(); foreach (var r in rows) s.Children.Add(r);
        return Panel(s, new Thickness(0));
    }

    public static async Task<ContentDialogResult> ShowDialog(XamlRoot root, string title, UIElement content, string primary, string close = "Cancelar")
    {
        var d = new ContentDialog { XamlRoot = root, Title = title, Content = content, PrimaryButtonText = primary, CloseButtonText = close, DefaultButton = ContentDialogButton.Primary };
        return await d.ShowAsync();
    }

    /// <summary>Mostrado quando outro cliente salvou antes (HTTP 409). Nada foi sobrescrito.</summary>
    public static Task<ContentDialogResult> ShowConflict(XamlRoot root, string message)
    {
        var s = new StackPanel { Spacing = 8 };
        s.Children.Add(Text(message)); s.Children.Add(Text("Suas alterações não foram salvas. Carregue a versão atual, revise e edite novamente.", 13, "inkMuted"));
        return ShowDialog(root, "Registro alterado por outra pessoa", s, "Carregar versão atual", "Fechar");
    }

    public static TextBox Input(string header, string value = "", string placeholder = "") =>
        new() { Header = header, Text = value, PlaceholderText = placeholder, MinWidth = 320 };
}

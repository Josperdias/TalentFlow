using Microsoft.UI;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Animation;
using Microsoft.UI.Xaml.Shapes;
using TalentFlow.Core;
using TalentFlow.Windows.Styles;
using Windows.UI;

namespace TalentFlow.Windows;

/// <summary>Blocos de interface do design system "Aurora" (mesmos tokens do site e do Android).</summary>
public static class Ui
{
    public static IReadOnlyDictionary<string, Color> Palette =>
        Application.Current.RequestedTheme == ApplicationTheme.Dark ? TfTokens.Dark : TfTokens.Light;

    public static SolidColorBrush Brush(string key) => new(Palette[key]);
    // Fontes embutidas (OFL) em Assets\Fonts. Se o Windows não resolver o arquivo, cai para Segoe/Georgia sem quebrar a tela.
    private static FontFamily Face(string file, string fallback, params string[] names) =>
        new(string.Join(", ", names.Select(n => $"ms-appx:///Assets/Fonts/{file}.ttf#{n}")) + ", " + fallback);
    public static readonly FontFamily Sans = Face("plus_jakarta_sans_regular", "Segoe UI Variable, Segoe UI", "Plus Jakarta Sans");
    public static readonly FontFamily SansMedium = Face("plus_jakarta_sans_medium", "Segoe UI Variable, Segoe UI", "Plus Jakarta Sans Medium", "Plus Jakarta Sans");
    public static readonly FontFamily SansSemiBold = Face("plus_jakarta_sans_semibold", "Segoe UI Variable, Segoe UI", "Plus Jakarta Sans SemiBold", "Plus Jakarta Sans");
    public static readonly FontFamily SansBold = Face("plus_jakarta_sans_bold", "Segoe UI Variable, Segoe UI", "Plus Jakarta Sans");
    public static readonly FontFamily SansExtraBold = Face("plus_jakarta_sans_extrabold", "Segoe UI Variable, Segoe UI", "Plus Jakarta Sans ExtraBold", "Plus Jakarta Sans");
    public static readonly FontFamily Serif = Face("fraunces_semibold", "Georgia", "Fraunces SemiBold", "Fraunces");
    public static readonly FontFamily Mono = new("Cascadia Mono, Consolas");

    private static FontFamily FaceFor(ushort weight) => weight switch { >= 800 => SansExtraBold, >= 700 => SansBold, >= 600 => SansSemiBold, >= 500 => SansMedium, _ => Sans };

    /// <summary>Entrada animada só na primeira carga de uma página (recargas por sincronização não re-animam).</summary>
    public static bool Entrance { get; set; } = true;
    private static readonly bool Motion = SafeMotion();
    private static bool SafeMotion() { try { return new global::Windows.UI.ViewManagement.UISettings().AnimationsEnabled; } catch { return true; } }

    public static LinearGradientBrush Gradient(Color a, Color b, bool vertical = false) => new()
    {
        StartPoint = new global::Windows.Foundation.Point(0, 0), EndPoint = vertical ? new global::Windows.Foundation.Point(0, 1) : new global::Windows.Foundation.Point(1, 1),
        GradientStops = { new GradientStop { Color = a, Offset = 0 }, new GradientStop { Color = b, Offset = 1 } }
    };

    /// <summary>Sobe e aparece (520 ms), em cascata pelo atraso. Respeita "mostrar animações" do Windows.</summary>
    public static T RiseIn<T>(this T e, int delayMs = 0) where T : FrameworkElement
    {
        if (!Entrance || !Motion) return e;
        e.Opacity = 0;
        var move = new TranslateTransform { Y = 22 };
        e.RenderTransform = move;
        e.Loaded += (_, _) =>
        {
            var ease = new CubicEase { EasingMode = EasingMode.EaseOut };
            var begin = TimeSpan.FromMilliseconds(delayMs); var dur = new Duration(TimeSpan.FromMilliseconds(520));
            var fade = new DoubleAnimation { To = 1, Duration = dur, BeginTime = begin, EasingFunction = ease };
            Storyboard.SetTarget(fade, e); Storyboard.SetTargetProperty(fade, "Opacity");
            var rise = new DoubleAnimation { To = 0, Duration = dur, BeginTime = begin, EasingFunction = ease };
            Storyboard.SetTarget(rise, move); Storyboard.SetTargetProperty(rise, "Y");
            var sb = new Storyboard(); sb.Children.Add(fade); sb.Children.Add(rise); sb.Begin();
        };
        return e;
    }

    public static TextBlock Text(string text, double size = 14, string color = "ink", global::Windows.UI.Text.FontWeight? weight = null, bool wrap = true)
    {
        var w = weight ?? FontWeights.Normal;
        return new() { Text = text, FontSize = size, Foreground = Brush(color), FontFamily = FaceFor(w.Weight), FontWeight = w, TextWrapping = wrap ? TextWrapping.Wrap : TextWrapping.NoWrap };
    }

    public static TextBlock Eyebrow(string text) =>
        new() { Text = text.ToUpperInvariant(), FontFamily = SansBold, FontWeight = FontWeights.Bold, FontSize = 11, CharacterSpacing = 160, Foreground = Brush("brand"), Margin = new Thickness(0, 6, 0, 2) };

    public static TextBlock Serifed(string text, double size, string color = "ink") =>
        new() { Text = text, FontFamily = Serif, FontSize = size, FontWeight = FontWeights.SemiBold, Foreground = Brush(color), TextWrapping = TextWrapping.Wrap };

    public static Border Panel(UIElement child, Thickness? padding = null) => new()
    {
        Background = Brush("surface"), BorderBrush = Brush("line"), BorderThickness = new Thickness(1),
        CornerRadius = new CornerRadius(TfTokens.RadiusXl), Padding = padding ?? new Thickness(20), Child = child
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
            Background = Brush(bg), CornerRadius = new CornerRadius(999),
            Padding = new Thickness(10, 2, 10, 3), HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Center,
            Child = new TextBlock { Text = text, FontSize = 11.5, FontFamily = SansBold, FontWeight = FontWeights.Bold, Foreground = Brush(fg) }
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
            Background = Brush(bg), BorderBrush = Brush(fg), BorderThickness = new Thickness(4, 1, 1, 1), CornerRadius = new CornerRadius(TfTokens.RadiusLg),
            Padding = new Thickness(14, 10, 14, 10), Margin = new Thickness(0, 0, 0, 12), Child = stack
        };
    }

    public static Button PrimaryButton(string text, Action onClick)
    {
        // Gradiente de ação: branco sobre #5846D4 -> #6C58F0 mantém contraste AA (>= 4,89:1).
        var normal = Gradient(Palette["brand"], Color.FromArgb(255, 0x6C, 0x58, 0xF0));
        var hover = Gradient(Palette["brandStrong"], Palette["brand"]);
        var b = new Button
        {
            Content = text, Background = normal, Foreground = Brush("onBrand"), BorderThickness = new Thickness(0), FontFamily = SansBold, FontWeight = FontWeights.Bold,
            CornerRadius = new CornerRadius(TfTokens.RadiusMd + 2), Padding = new Thickness(20, 9, 20, 9)
        };
        b.Resources["ButtonBackgroundPointerOver"] = hover; b.Resources["ButtonBackgroundPressed"] = hover;
        b.Resources["ButtonForegroundPointerOver"] = Brush("onBrand"); b.Resources["ButtonForegroundPressed"] = Brush("onBrand");
        b.Resources["ButtonBorderBrushPointerOver"] = new SolidColorBrush(Microsoft.UI.Colors.Transparent); b.Resources["ButtonBorderBrushPressed"] = new SolidColorBrush(Microsoft.UI.Colors.Transparent);
        b.Click += (_, _) => onClick();
        return b;
    }

    public static Button SecondaryButton(string text, Action onClick)
    {
        var b = new Button { Content = text, Background = Brush("surface"), Foreground = Brush("ink"), BorderBrush = Brush("line"), FontFamily = SansSemiBold, FontWeight = FontWeights.SemiBold, CornerRadius = new CornerRadius(TfTokens.RadiusMd + 2), Padding = new Thickness(18, 8, 18, 8) };
        b.Click += (_, _) => onClick();
        return b;
    }

    public static StackPanel PageHeader(string eyebrow, string title, string? lead = null, params UIElement[] actions)
    {
        var text = new StackPanel { Spacing = 4 };
        text.Children.Add(Eyebrow(eyebrow)); text.Children.Add(Serifed(title, 34));
        if (!string.IsNullOrEmpty(lead)) text.Children.Add(Text(lead, 14, "inkMuted"));
        var row = new Grid { ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }, new ColumnDefinition { Width = GridLength.Auto } } };
        row.Children.Add(text);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, VerticalAlignment = VerticalAlignment.Bottom };
        foreach (var a in actions) buttons.Children.Add(a);
        Grid.SetColumn(buttons, 1); row.Children.Add(buttons);
        var outer = new StackPanel { Spacing = 12, Margin = new Thickness(0, 0, 0, 20) };
        outer.Children.Add(row);
        return outer.RiseIn();
    }

    public static UIElement Loading() => new StackPanel { Padding = new Thickness(0, 40, 0, 0), HorizontalAlignment = HorizontalAlignment.Center, Children = { new ProgressRing { IsActive = true, Width = 36, Height = 36 } } };

    public static UIElement Empty(string title, string text = "")
    {
        var s = new StackPanel { Spacing = 4, HorizontalAlignment = HorizontalAlignment.Center };
        s.Children.Add(Text(title, 15, "ink", FontWeights.SemiBold));
        if (text.Length > 0) s.Children.Add(Text(text, 13, "inkMuted"));
        return new Border { BorderBrush = Brush("lineStrong"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(TfTokens.RadiusXl), Padding = new Thickness(32), Child = s };
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
        var fig = Text(figure, 22, "ink", FontWeights.Bold); fig.VerticalAlignment = VerticalAlignment.Center; fig.TextAlignment = TextAlignment.Right; Grid.SetColumn(fig, 1); g.Children.Add(fig);
        return new Border { BorderBrush = Brush("line"), BorderThickness = new Thickness(0, 0, 0, last ? 0 : 1), Child = g };
    }

    public static Border Ledger(params UIElement[] rows)
    {
        var s = new StackPanel(); foreach (var r in rows) s.Children.Add(r);
        return Panel(s, new Thickness(0));
    }

    /// <summary>Marca do produto: tile em gradiente com o fluxo (mesmo desenho do site e do Android).</summary>
    public static UIElement Mark(double size = 38)
    {
        var k = size / 40.0;
        var host = new Grid { Width = size, Height = size };
        host.Children.Add(new Border { CornerRadius = new CornerRadius(size * 0.3), Background = Gradient(Color.FromArgb(255, 0x6C, 0x58, 0xF0), Color.FromArgb(255, 0xB2, 0x7B, 0xF5)) });
        var c = new Canvas { Width = size, Height = size, HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Top };
        var white = new SolidColorBrush(Microsoft.UI.Colors.White);
        Line Ln(double x1, double y1, double x2, double y2) => new() { X1 = x1 * k, Y1 = y1 * k, X2 = x2 * k, Y2 = y2 * k, Stroke = white, StrokeThickness = 3.6 * k, StrokeStartLineCap = PenLineCap.Round, StrokeEndLineCap = PenLineCap.Round };
        Ellipse Dot(double cx, double cy, double r, double a) { var d = new Ellipse { Width = 2 * r * k, Height = 2 * r * k, Fill = white, Opacity = a }; Canvas.SetLeft(d, (cx - r) * k); Canvas.SetTop(d, (cy - r) * k); return d; }
        c.Children.Add(Ln(11, 12, 29, 12)); c.Children.Add(Ln(20, 12, 20, 28)); c.Children.Add(Dot(29, 28, 3.2, .92)); c.Children.Add(Dot(11, 28, 2.2, .55));
        host.Children.Add(c);
        return host;
    }

    /// <summary>Iniciais sobre cor estável por nome (decorativo: o nome sempre aparece em texto ao lado).</summary>
    public static UIElement Avatar(string name, double size = 36)
    {
        Color[] palette = [Color.FromArgb(255, 0x58, 0x46, 0xD4), Color.FromArgb(255, 0x0B, 0x6B, 0x63), Color.FromArgb(255, 0x2A, 0x63, 0xA8), Color.FromArgb(255, 0xB0, 0x36, 0x4B), Color.FromArgb(255, 0x8A, 0x5A, 0x12), Color.FromArgb(255, 0x3D, 0x4A, 0x7A)];
        var baseColor = palette[name.Sum(ch => (int)ch) % palette.Length];
        var initials = string.Concat(name.Split(' ', StringSplitOptions.RemoveEmptyEntries).Take(2).Select(p => char.ToUpperInvariant(p[0])));
        return new Border
        {
            Width = size, Height = size, CornerRadius = new CornerRadius(size / 2), Background = Gradient(baseColor, Color.FromArgb(255, (byte)(baseColor.R * 0.7 + 76), (byte)(baseColor.G * 0.7 + 76), (byte)(baseColor.B * 0.7 + 76))),
            Child = new TextBlock { Text = initials.Length == 0 ? "·" : initials, FontSize = size * 0.38, FontFamily = SansBold, FontWeight = FontWeights.Bold, Foreground = new SolidColorBrush(Microsoft.UI.Colors.White), HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center }
        };
    }

    /// <summary>Cartão de indicador: faixa de cor de significado, número grande e nota. <c>value</c> já vem tratado ("—" sem dado).</summary>
    public static Border Kpi(string label, string value, string note, string tone = "brand", int delayMs = 0)
    {
        var accent = (tone is "positive" or "attention" or "info") ? tone : "brand";
        var body = new StackPanel { Spacing = 4, Padding = new Thickness(20, 16, 16, 16) };
        body.Children.Add(Text(label, 13, "inkMuted", FontWeights.SemiBold));
        var v = Text(value, 38, "ink", FontWeights.ExtraBold); v.CharacterSpacing = -30; body.Children.Add(v);
        body.Children.Add(Text(note, 12, "inkMuted"));
        var grid = new Grid { ColumnDefinitions = { new ColumnDefinition { Width = new GridLength(5) }, new ColumnDefinition() } };
        grid.Children.Add(new Border { Background = Brush(accent), CornerRadius = new CornerRadius(TfTokens.RadiusXl, 0, 0, TfTokens.RadiusXl) });
        Grid.SetColumn(body, 1); grid.Children.Add(body);
        return new Border { Background = Brush("surface"), BorderBrush = Brush("line"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(TfTokens.RadiusXl), MinHeight = 124, Child = grid }.RiseIn(delayMs);
    }

    public static Grid KpiGrid(int columns, params UIElement[] cards)
    {
        var g = new Grid { ColumnSpacing = 16, RowSpacing = 16 };
        for (var c = 0; c < columns; c++) g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        for (var r = 0; r < (cards.Length + columns - 1) / columns; r++) g.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        for (var i = 0; i < cards.Length; i++) { Grid.SetColumn((FrameworkElement)cards[i], i % columns); Grid.SetRow((FrameworkElement)cards[i], i / columns); g.Children.Add(cards[i]); }
        return g;
    }

    /// <summary>Barra horizontal que cresce da esquerda (animada só na primeira carga).</summary>
    public static Grid GrowBar(double fraction, int delayMs = 0)
    {
        var fill = new Border { Background = Gradient(Palette["brand"], Palette["accent"]), HorizontalAlignment = HorizontalAlignment.Left, Width = 0, CornerRadius = new CornerRadius(6) };
        var track = new Grid { Height = 12, Background = Brush("sunken"), CornerRadius = new CornerRadius(6), VerticalAlignment = VerticalAlignment.Center };
        track.Children.Add(fill);
        var played = false;
        track.SizeChanged += (_, e) =>
        {
            var target = Math.Max(4, e.NewSize.Width * fraction);
            if (played || !Entrance || !Motion) { fill.Width = target; return; }
            played = true;
            var a = new DoubleAnimation { To = target, Duration = new Duration(TimeSpan.FromMilliseconds(900)), BeginTime = TimeSpan.FromMilliseconds(delayMs), EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }, EnableDependentAnimation = true };
            Storyboard.SetTarget(a, fill); Storyboard.SetTargetProperty(a, "Width");
            var sb = new Storyboard(); sb.Children.Add(a); sb.Begin();
        };
        return track;
    }

    private static Microsoft.UI.Xaml.Shapes.Path Arc(double startDeg, double sweepDeg, double r, double c, Microsoft.UI.Xaml.Media.Brush brush, double stroke)
    {
        var a0 = startDeg * Math.PI / 180; var a1 = (startDeg + sweepDeg) * Math.PI / 180;
        var fig = new PathFigure { StartPoint = new global::Windows.Foundation.Point(c + r * Math.Cos(a0), c + r * Math.Sin(a0)), IsClosed = false };
        fig.Segments.Add(new ArcSegment { Point = new global::Windows.Foundation.Point(c + r * Math.Cos(a1), c + r * Math.Sin(a1)), Size = new global::Windows.Foundation.Size(r, r), SweepDirection = SweepDirection.Clockwise, IsLargeArc = sweepDeg > 180 });
        var geo = new PathGeometry(); geo.Figures.Add(fig);
        return new Microsoft.UI.Xaml.Shapes.Path { Data = geo, Stroke = brush, StrokeThickness = stroke, StrokeStartLineCap = PenLineCap.Round, StrokeEndLineCap = PenLineCap.Round, HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Top };
    }

    /// <summary>Rosca desenhada com arcos. Sem dados: anel vazio e "—".</summary>
    public static UIElement Donut(IReadOnlyList<(string Label, int Value, Color Color)> slices, string centerLabel)
    {
        const double size = 136, stroke = 15, r = (size - stroke) / 2;
        var total = slices.Sum(s => s.Value);
        var host = new Grid { Width = size, Height = size };
        host.Children.Add(new Ellipse { Width = size - stroke, Height = size - stroke, Stroke = Brush("sunken"), StrokeThickness = stroke, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center });
        if (total > 0)
        {
            double start = -90;
            foreach (var s in slices.Where(x => x.Value > 0))
            {
                var sweep = 360.0 * s.Value / total;
                if (sweep >= 359.9) host.Children.Add(new Ellipse { Width = size - stroke, Height = size - stroke, Stroke = new SolidColorBrush(s.Color), StrokeThickness = stroke, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center });
                else host.Children.Add(Arc(start, Math.Max(sweep - 3, 0.5), r, size / 2, new SolidColorBrush(s.Color), stroke));
                start += sweep;
            }
        }
        var center = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };
        var big = Serifed(total == 0 ? "—" : total.ToString(), 26); big.HorizontalAlignment = HorizontalAlignment.Center;
        var small = Text(centerLabel, 11, "inkMuted"); small.HorizontalAlignment = HorizontalAlignment.Center;
        center.Children.Add(big); center.Children.Add(small); host.Children.Add(center);
        return host.RiseIn(200);
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

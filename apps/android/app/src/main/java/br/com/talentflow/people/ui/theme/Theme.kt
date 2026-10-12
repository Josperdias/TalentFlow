package br.com.talentflow.people.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Paleta própria do TalentFlow (tokens compartilhados com web e Windows) além do que o Material 3 cobre. */
val LocalTf = staticCompositionLocalOf { TfTokens.Light }

private val TfShapes = Shapes(
    extraSmall = androidx.compose.foundation.shape.RoundedCornerShape(2.dp),
    small = androidx.compose.foundation.shape.RoundedCornerShape(4.dp),
    medium = androidx.compose.foundation.shape.RoundedCornerShape(4.dp),
    large = androidx.compose.foundation.shape.RoundedCornerShape(6.dp),
    extraLarge = androidx.compose.foundation.shape.RoundedCornerShape(6.dp),
)

/** Serifa (títulos e números) + sans do sistema (interface) + mono (rótulos e códigos): mesma hierarquia do site. */
private val TfTypography = Typography(
    displaySmall = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 32.sp, lineHeight = 38.sp),
    headlineMedium = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 26.sp, lineHeight = 32.sp),
    headlineSmall = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 20.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontWeight = FontWeight.Medium, fontSize = 16.sp, lineHeight = 22.sp),
    titleSmall = TextStyle(fontWeight = FontWeight.Medium, fontSize = 14.sp, lineHeight = 20.sp),
    bodyLarge = TextStyle(fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge = TextStyle(fontWeight = FontWeight.Medium, fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontWeight = FontWeight.Medium, fontSize = 12.sp, lineHeight = 16.sp),
    labelSmall = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 11.sp, lineHeight = 14.sp, letterSpacing = 1.sp),
)

@Composable
fun TalentFlowTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    val p = if (dark) TfTokens.Dark else TfTokens.Light
    val scheme = if (dark) darkColorScheme(
        primary = p.brand, onPrimary = p.onBrand, primaryContainer = p.brandSoft, onPrimaryContainer = p.brandStrong,
        secondary = p.brand, onSecondary = p.onBrand, secondaryContainer = p.brandSoft, onSecondaryContainer = p.brandStrong,
        background = p.canvas, onBackground = p.ink, surface = p.surface, onSurface = p.ink,
        surfaceVariant = p.sunken, onSurfaceVariant = p.inkMuted, outline = p.lineStrong, outlineVariant = p.line,
        error = p.critical, errorContainer = p.criticalSoft, onError = p.canvas, onErrorContainer = p.critical,
        surfaceContainer = p.surface, surfaceContainerHigh = p.surface, surfaceContainerLow = p.canvas, surfaceContainerHighest = p.sunken,
    ) else lightColorScheme(
        primary = p.brand, onPrimary = p.onBrand, primaryContainer = p.brandSoft, onPrimaryContainer = p.brandStrong,
        secondary = p.brand, onSecondary = p.onBrand, secondaryContainer = p.brandSoft, onSecondaryContainer = p.brandStrong,
        background = p.canvas, onBackground = p.ink, surface = p.surface, onSurface = p.ink,
        surfaceVariant = p.sunken, onSurfaceVariant = p.inkMuted, outline = p.lineStrong, outlineVariant = p.line,
        error = p.critical, errorContainer = p.criticalSoft, onError = p.surface, onErrorContainer = p.critical,
        surfaceContainer = p.surface, surfaceContainerHigh = p.surface, surfaceContainerLow = p.canvas, surfaceContainerHighest = p.sunken,
    )
    CompositionLocalProvider(LocalTf provides p) {
        MaterialTheme(colorScheme = scheme, typography = TfTypography, shapes = TfShapes, content = content)
    }
}

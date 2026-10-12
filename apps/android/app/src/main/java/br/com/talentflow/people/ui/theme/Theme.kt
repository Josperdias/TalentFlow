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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.com.talentflow.people.R

/** Paleta própria do TalentFlow (tokens compartilhados com web e Windows) além do que o Material 3 cobre. */
val LocalTf = staticCompositionLocalOf { TfTokens.Light }

/** Plus Jakarta Sans (interface) e Fraunces (títulos e marca): as mesmas famílias do site, embutidas no app (OFL). */
val Jakarta = FontFamily(
    Font(R.font.plus_jakarta_sans_regular, FontWeight.Normal),
    Font(R.font.plus_jakarta_sans_medium, FontWeight.Medium),
    Font(R.font.plus_jakarta_sans_semibold, FontWeight.SemiBold),
    Font(R.font.plus_jakarta_sans_bold, FontWeight.Bold),
    Font(R.font.plus_jakarta_sans_extrabold, FontWeight.ExtraBold),
)
val Fraunces = FontFamily(
    Font(R.font.fraunces_semibold, FontWeight.SemiBold),
    Font(R.font.fraunces_semibold, FontWeight.Normal),
    Font(R.font.fraunces_semibold, FontWeight.Bold),
)

private val TfShapes = Shapes(
    extraSmall = RoundedCornerShape(TfTokens.RADIUS_SM.dp),
    small = RoundedCornerShape(TfTokens.RADIUS_MD.dp),
    medium = RoundedCornerShape(TfTokens.RADIUS_LG.dp),
    large = RoundedCornerShape(TfTokens.RADIUS_XL.dp),
    extraLarge = RoundedCornerShape(28.dp),
)

private val TfTypography = Typography(
    displayMedium = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.ExtraBold, fontSize = 34.sp, lineHeight = 38.sp, letterSpacing = (-1).sp),
    displaySmall = TextStyle(fontFamily = Fraunces, fontWeight = FontWeight.SemiBold, fontSize = 34.sp, lineHeight = 40.sp, letterSpacing = (-0.5).sp),
    headlineMedium = TextStyle(fontFamily = Fraunces, fontWeight = FontWeight.SemiBold, fontSize = 28.sp, lineHeight = 34.sp, letterSpacing = (-0.4).sp),
    headlineSmall = TextStyle(fontFamily = Fraunces, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = Fraunces, fontWeight = FontWeight.SemiBold, fontSize = 20.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.Bold, fontSize = 16.sp, lineHeight = 22.sp),
    titleSmall = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    bodyLarge = TextStyle(fontFamily = Jakarta, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = Jakarta, fontSize = 14.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontFamily = Jakarta, fontSize = 12.sp, lineHeight = 17.sp),
    labelLarge = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.Bold, fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.Bold, fontSize = 12.sp, lineHeight = 16.sp),
    labelSmall = TextStyle(fontFamily = Jakarta, fontWeight = FontWeight.Bold, fontSize = 11.sp, lineHeight = 14.sp, letterSpacing = 1.6.sp),
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

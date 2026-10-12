// GERADO por packages/design-tokens/build.mjs — não edite à mão.
package br.com.talentflow.people.ui.theme

import androidx.compose.ui.graphics.Color

data class TfPalette(
    val canvas: Color,
    val surface: Color,
    val sunken: Color,
    val line: Color,
    val lineStrong: Color,
    val ink: Color,
    val inkMuted: Color,
    val inkFaint: Color,
    val brand: Color,
    val brandStrong: Color,
    val brandSoft: Color,
    val onBrand: Color,
    val attention: Color,
    val attentionSoft: Color,
    val positive: Color,
    val positiveSoft: Color,
    val critical: Color,
    val criticalSoft: Color,
    val info: Color,
    val infoSoft: Color,
    val focus: Color
)

object TfTokens {
    val Light = TfPalette(
        canvas = Color(0xFFF4F5F2),
        surface = Color(0xFFFFFFFF),
        sunken = Color(0xFFE9ECE8),
        line = Color(0xFFD5DAD4),
        lineStrong = Color(0xFF788580),
        ink = Color(0xFF142120),
        inkMuted = Color(0xFF4C5B57),
        inkFaint = Color(0xFF56645F),
        brand = Color(0xFF0B4F5C),
        brandStrong = Color(0xFF073A44),
        brandSoft = Color(0xFFDAE9EA),
        onBrand = Color(0xFFFFFFFF),
        attention = Color(0xFF85570F),
        attentionSoft = Color(0xFFF3E7CF),
        positive = Color(0xFF256B49),
        positiveSoft = Color(0xFFDCEBE2),
        critical = Color(0xFFA5342A),
        criticalSoft = Color(0xFFF4DCD8),
        info = Color(0xFF2A6390),
        infoSoft = Color(0xFFDCE8F2),
        focus = Color(0xFF0B6FD6)
    )

    val Dark = TfPalette(
        canvas = Color(0xFF0D1514),
        surface = Color(0xFF142120),
        sunken = Color(0xFF0A1110),
        line = Color(0xFF26373A),
        lineStrong = Color(0xFF5F7B80),
        ink = Color(0xFFE8EEEC),
        inkMuted = Color(0xFFA8B8B3),
        inkFaint = Color(0xFF8A9C97),
        brand = Color(0xFF5BB6C4),
        brandStrong = Color(0xFF8ACFDA),
        brandSoft = Color(0xFF143A41),
        onBrand = Color(0xFF06262C),
        attention = Color(0xFFE0AE5B),
        attentionSoft = Color(0xFF3A2E16),
        positive = Color(0xFF6FC49A),
        positiveSoft = Color(0xFF17342A),
        critical = Color(0xFFF0958B),
        criticalSoft = Color(0xFF401D19),
        info = Color(0xFF7FB4DE),
        infoSoft = Color(0xFF15303F),
        focus = Color(0xFF7DB8FF)
    )

    /** Espaçamentos em dp. */
    const val S1 = 4; const val S2 = 8; const val S3 = 12; const val S4 = 16
    const val S5 = 24; const val S6 = 32; const val S7 = 48
    const val RADIUS_SM = 2; const val RADIUS_MD = 4; const val RADIUS_LG = 6
    const val TOUCH_TARGET = 48
}

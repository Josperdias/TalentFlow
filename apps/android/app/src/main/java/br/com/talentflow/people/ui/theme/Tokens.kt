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
    val accent: Color,
    val attention: Color,
    val attentionSoft: Color,
    val positive: Color,
    val positiveSoft: Color,
    val critical: Color,
    val criticalSoft: Color,
    val info: Color,
    val infoSoft: Color,
    val focus: Color,
    val nav: Color,
    val navRaised: Color,
    val navInk: Color,
    val navMuted: Color,
    val navLine: Color,
    val navActive: Color,
    val navActiveInk: Color
)

object TfTokens {
    val Light = TfPalette(
        canvas = Color(0xFFF3F4FA),
        surface = Color(0xFFFFFFFF),
        sunken = Color(0xFFECEEF8),
        line = Color(0xFFE1E4F0),
        lineStrong = Color(0xFF7C86A6),
        ink = Color(0xFF141B34),
        inkMuted = Color(0xFF48527A),
        inkFaint = Color(0xFF586285),
        brand = Color(0xFF5846D4),
        brandStrong = Color(0xFF4333B3),
        brandSoft = Color(0xFFECE9FF),
        onBrand = Color(0xFFFFFFFF),
        accent = Color(0xFF8B6CF0),
        attention = Color(0xFF8A5A12),
        attentionSoft = Color(0xFFFBEFD9),
        positive = Color(0xFF12694D),
        positiveSoft = Color(0xFFDDF3EA),
        critical = Color(0xFFB0364B),
        criticalSoft = Color(0xFFFBE3E7),
        info = Color(0xFF2A63A8),
        infoSoft = Color(0xFFE0ECFA),
        focus = Color(0xFF2F6BFF),
        nav = Color(0xFF0E1530),
        navRaised = Color(0xFF18214A),
        navInk = Color(0xFFDCE1F7),
        navMuted = Color(0xFF98A3CC),
        navLine = Color(0xFF26305E),
        navActive = Color(0xFF2B2F7A),
        navActiveInk = Color(0xFFFFFFFF)
    )

    val Dark = TfPalette(
        canvas = Color(0xFF090E20),
        surface = Color(0xFF111937),
        sunken = Color(0xFF0C1230),
        line = Color(0xFF232C58),
        lineStrong = Color(0xFF6B79AA),
        ink = Color(0xFFE9ECFA),
        inkMuted = Color(0xFFB2BAD9),
        inkFaint = Color(0xFF98A2C8),
        brand = Color(0xFFA99CFF),
        brandStrong = Color(0xFFC4BAFF),
        brandSoft = Color(0xFF241F5E),
        onBrand = Color(0xFF150F4A),
        accent = Color(0xFF8B6CF0),
        attention = Color(0xFFE7B568),
        attentionSoft = Color(0xFF3A2C14),
        positive = Color(0xFF6FD3AA),
        positiveSoft = Color(0xFF10352A),
        critical = Color(0xFFF59BAB),
        criticalSoft = Color(0xFF42171F),
        info = Color(0xFF86B6EE),
        infoSoft = Color(0xFF14305A),
        focus = Color(0xFF8FB0FF),
        nav = Color(0xFF070B1B),
        navRaised = Color(0xFF111937),
        navInk = Color(0xFFDCE1F7),
        navMuted = Color(0xFF98A3CC),
        navLine = Color(0xFF1D264F),
        navActive = Color(0xFF2B2F7A),
        navActiveInk = Color(0xFFFFFFFF)
    )

    /** Espaçamentos em dp. */
    const val S1 = 4; const val S2 = 8; const val S3 = 12; const val S4 = 16
    const val S5 = 24; const val S6 = 32; const val S7 = 48
    const val RADIUS_SM = 6; const val RADIUS_MD = 10; const val RADIUS_LG = 14; const val RADIUS_XL = 20
    const val TOUCH_TARGET = 48
}

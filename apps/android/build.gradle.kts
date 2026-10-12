plugins {
    // Todos os plugins na raiz (apply false) para compartilharem o mesmo classloader.
    // O Kotlin Android precisa enxergar as classes do AGP; sem isto: "com/android/build/gradle/api/BaseVariant".
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.kotlin.jvm) apply false
}

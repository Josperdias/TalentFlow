plugins {
    // Plugins Kotlin (Maven Central / Gradle Plugin Portal) ficam na raiz para compartilhar o classloader.
    // O plugin Android (AGP) é declarado apenas no módulo :app.
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.kotlin.jvm) apply false
}

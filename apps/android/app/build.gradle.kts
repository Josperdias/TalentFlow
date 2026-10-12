import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

// Versão única do produto (arquivo VERSION na raiz do repositório): "1.3.0-rc.1"
val productVersion = rootProject.file("../../VERSION").readText().trim()
val versionNumbers = Regex("""(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?""").matchEntire(productVersion)
    ?: error("VERSION inválido: $productVersion")
val (maj, min, pat) = versionNumbers.destructured
// versionCode cresce a cada rc e a versão final vale mais que qualquer rc: 1.3.0-rc.1 -> 1030001, 1.3.0 -> 1030099
val computedCode = (maj.toInt() * 10000 + min.toInt() * 100 + pat.toInt()) * 100 + (versionNumbers.groupValues[4].toIntOrNull() ?: 99)

// Assinatura de release: SOMENTE por variáveis de ambiente (GitHub Actions Secrets). Nada de keystore no repositório.
val keystorePath = System.getenv("TF_KEYSTORE_PATH")
val hasSigning = !keystorePath.isNullOrBlank() && file(keystorePath).exists()

android {
    namespace = "br.com.talentflow.people"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.com.talentflow.people"
        minSdk = 26
        targetSdk = 35
        versionCode = computedCode
        versionName = productVersion
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        if (hasSigning) {
            create("release") {
                storeFile = file(keystorePath!!)
                storePassword = System.getenv("TF_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("TF_KEY_ALIAS")
                keyPassword = System.getenv("TF_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false // R8 será ligado após validação em aparelho/emulador (ver docs/STATUS.md)
            if (hasSigning) signingConfig = signingConfigs.getByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    lint { abortOnError = false; checkReleaseBuilds = false }
    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
}

kotlin { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }

dependencies {
    implementation(project(":core"))
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test:runner:1.6.2")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

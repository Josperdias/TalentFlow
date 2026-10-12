val coreOnly = providers.gradleProperty("coreOnly").orNull == "true"

pluginManagement {
    val coreOnlyPM = providers.gradleProperty("coreOnly").orNull == "true"
    repositories {
        if (!coreOnlyPM) google()   // AGP/androidx vêm do Google; indisponível em alguns ambientes restritos
        mavenCentral(); gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        if (!coreOnly) google()
        mavenCentral()
    }
}
rootProject.name = "talentflow-android"
include(":core")
// O módulo Android depende do SDK/AGP (dl.google.com). Sem acesso, compile só o :core:  ./gradlew -PcoreOnly=true :core:test
if (!coreOnly) include(":app")

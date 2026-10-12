// Usado apenas com -PcoreOnly=true (ambientes sem acesso ao repositório Google/AGP): só o módulo :core.
plugins {
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.kotlin.jvm) apply false
}

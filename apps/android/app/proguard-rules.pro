# R8 ainda desligado (ver build.gradle.kts). Regras preparadas para quando for ligado:
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keep,includedescriptorclasses class br.com.talentflow.core.**$$serializer { *; }
-keepclassmembers class br.com.talentflow.core.** { *** Companion; }
-dontwarn okhttp3.**
-dontwarn okio.**

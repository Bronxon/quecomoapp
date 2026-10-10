plugins {
    id("com.android.application")
}

fun propiedad(nombre: String): String =
    providers.gradleProperty(nombre).orNull?.trim()?.takeIf { it.isNotEmpty() }
        ?: error("Falta la propiedad «$nombre» en android/gradle.properties")

val paquete = propiedad("quecomo.applicationId")
val dominio = propiedad("quecomo.host").removePrefix("https://").removeSuffix("/")
val urlInicio = "https://$dominio/"

// Declaración de Digital Asset Links del lado de la app (el sitio publica la
// contraparte en https://<dominio>/.well-known/assetlinks.json).
val declaracionSitio =
    """[{ \"relation\": [\"delegate_permission/common.handle_all_urls\"], """ +
        """\"target\": { \"namespace\": \"web\", \"site\": \"https://$dominio\" } }]"""

// Firma con la llave de SUBIDA (upload key). Google Play vuelve a firmar la
// app con su propia llave (Play App Signing). Se configura con variables de
// entorno para no guardar contraseñas en el repositorio.
val almacenLlaves: String? = System.getenv("QUECOMO_KEYSTORE")?.takeIf { it.isNotBlank() }

android {
    namespace = "mx.quecomo.twa"
    compileSdk = 36

    defaultConfig {
        applicationId = paquete
        minSdk = 24
        targetSdk = 36 // Google Play exige API 36 desde el 31/08/2026
        versionCode = propiedad("quecomo.versionCode").toInt()
        versionName = propiedad("quecomo.versionName")

        manifestPlaceholders["dominio"] = dominio
        resValue("string", "launchUrl", urlInicio)
        resValue("string", "assetStatements", declaracionSitio)
        resValue("string", "providerAuthority", "$paquete.fileprovider")
    }

    signingConfigs {
        if (almacenLlaves != null) {
            create("subida") {
                storeFile = file(almacenLlaves)
                storePassword = System.getenv("QUECOMO_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("QUECOMO_KEY_ALIAS")
                keyPassword = System.getenv("QUECOMO_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            if (almacenLlaves != null) {
                signingConfig = signingConfigs.getByName("subida")
            }
        }
    }

    buildFeatures {
        resValues = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    // Biblioteca oficial de Google para Trusted Web Activities.
    implementation("com.google.androidbrowserhelper:androidbrowserhelper:2.7.3")
}

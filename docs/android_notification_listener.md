# Android Bank Notification Automation Guide (Fase 15)

Este documento detalla la arquitectura, el código nativo en Kotlin y las alternativas de automatización para capturar notificaciones bancarias en Android y enviarlas al backend FastAPI por Tailscale/LAN.

---

## 1. Arquitectura del Flujo

```
[ APLICACIÓN BANCARIA / SMS ]
       │
       ▼ (Notificación Push al Sistema Android)
[ ANDROID NOTIFICATION CENTER ]
       │
       ▼ (Intercepción de Notificaciones)
[ NotificationListenerService / MacroDroid Trigger ]
       │
       ▼ (HTTP POST payload: {"source": "bank", "content": "..."})
[ TÚNEL VPN SEGURO: TAILSCALE / LAN ]
       │
       ▼
[ BACKEND FASTAPI: POST /webhooks/bank ]
       │
       ▼
[ LLM STRUCTURED OUTPUT (Gemini / Ollama) ]
       │
       ▼
[ SUPABASE / POSTGRESQL (tabla 'transactions') ]
```

---

## 2. Opción A: Automatización Nativa con MacroDroid (Recomendada para Expo Go y Taller)

Dado que **Expo Go** es un cliente sandbox precompilado que no permite compilar código Java/Kotlin arbitrario en tiempo de ejecución, **MacroDroid** (disponible gratuitamente en Google Play Store) es la herramienta estándar para interceptar notificaciones nativas en el dispositivo físico sin requerir un entorno de desarrollo de Android Studio.

### Pasos de Configuración en el Teléfono Android:

1. **Instalar MacroDroid**:
   - Descarga **MacroDroid** desde Google Play Store en el mismo teléfono donde tienes Expo Go.
   - Otorga el permiso de **Acceso a Notificaciones** en los ajustes del sistema Android (Ajustes → Aplicaciones → Acceso especial → Acceso a notificaciones).

2. **Crear una Nueva Macro**:
   - Pulsa en **Añadir macro**.
   - Nombre de la macro: `Captura Webhook Bancario`.

3. **Configurar el Disparador (Trigger)**:
   - Toca el botón `+` en **Disparadores**.
   - Selecciona: **Notificación** → **Notificación recibida**.
   - Modo de selección:
     - *Opción recomendada*: Seleccionar las apps de tus bancos (ej: Bancolombia, Nequi, Nu Colombia, Davivienda, Mensajes de texto SMS).
     - *Filtro de texto*: Contiene palabras clave como: `compra`, `transferencia`, `cargo`, `abono`, `retiro`, `recibiste`.

4. **Configurar la Acción (Action)**:
   - Toca el botón `+` en **Acciones**.
   - Selecciona: **Conectividad** → **Solicitud HTTP (HTTP Request)**.
   - **Método HTTP**: `POST`.
   - **URL del Servidor**:
     - Con Tailscale activo: `http://<IP_TAILSCALE_DE_TU_PC>:8000/webhooks/bank`
     - En red local WiFi: `http://<IP_LOCAL_DE_TU_PC>:8000/webhooks/bank`
   - **Tipo de contenido (Content-Type)**: `application/json`.
   - **Cuerpo de la solicitud (Body)**:
     ```json
     {
       "source": "macrodroid_android",
       "content": "[notif_text]"
     }
     ```
     *(Nota: En MacroDroid, `[notif_text]` es la variable mágica que contiene el texto de la notificación capturada).*

5. **Guardar y Probar**:
   - Guarda la macro.
   - Envía o simula una notificación o realiza una transacción de prueba.
   - Abre la pantalla **Automatización Bancaria** (botón `🏦 Banco` en la app móvil) para ver la transacción extraída por el LLM y guardada en PostgreSQL en tiempo real.

---

## 3. Opción B: Implementación Nativa en Kotlin (`NotificationListenerService`)

Para proyectos con build personalizado de React Native (usando `npx expo prebuild` o Bare React Native), se utiliza la API oficial de Android: `android.service.notification.NotificationListenerService`.

### 3.1 Servicio Kotlin: `BankNotificationListenerService.kt`
Ubicación: `android/app/src/main/java/com/personalassistantai/BankNotificationListenerService.kt`

```kotlin
package com.personalassistantai

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

class BankNotificationListenerService : NotificationListenerService() {

    companion object {
        private const val TAG = "BankNotifListener"
        // IP de Tailscale o backend configurada
        private const val BACKEND_WEBHOOK_URL = "http://100.x.y.z:8000/webhooks/bank"
        private val JSON = "application/json; charset=utf-8".toMediaType()
    }

    private val httpClient = OkHttpClient()

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val packageName = sbn.packageName ?: ""
        val extras = sbn.notification.extras ?: return
        val title = extras.getString("android.title") ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""
        val fullContent = "$title $text".trim()

        // Filtrar paquetes de bancos o palabras financieras
        val isFinancialApp = packageName.contains("bancolombia") ||
                             packageName.contains("nequi") ||
                             packageName.contains("nu") ||
                             packageName.contains("davivienda") ||
                             packageName.contains("mms") || // SMS
                             packageName.contains("messaging")

        val containsFinancialKeywords = fullContent.contains("compra", ignoreCase = true) ||
                                         fullContent.contains("transferencia", ignoreCase = true) ||
                                         fullContent.contains("cargo", ignoreCase = true) ||
                                         fullContent.contains("abono", ignoreCase = true) ||
                                         fullContent.contains("recibiste", ignoreCase = true)

        if (isFinancialApp || containsFinancialKeywords) {
            Log.d(TAG, "Notificación financiera detectada de $packageName: $fullContent")
            dispatchWebhook(fullContent)
        }
    }

    private fun dispatchWebhook(content: String) {
        val payload = JSONObject().apply {
            put("source", "android_notification_listener")
            put("content", content)
        }

        val requestBody = payload.toString().toRequestBody(JSON)
        val request = Request.Builder()
            .url(BACKEND_WEBHOOK_URL)
            .post(requestBody)
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e(TAG, "Error enviando webhook bancario a $BACKEND_WEBHOOK_URL: ${e.message}")
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (response.isSuccessful) {
                        Log.i(TAG, "Webhook bancario procesado exitosamente: ${response.code}")
                    } else {
                        Log.w(TAG, "Webhook bancario retorno error: ${response.code}")
                    }
                }
            }
        })
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
    }
}
```

### 3.2 Declaración en `AndroidManifest.xml`
Ubicación: `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />

    <application>
        <!-- Registro del Servicio de Escucha de Notificaciones -->
        <service
            android:name=".BankNotificationListenerService"
            android:label="Asistente Personal Bank Notification Listener"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>
    </application>
</manifest>
```

---

## 4. Pruebas y Validación desde la Aplicación Móvil

Para facilitar la evaluación y demostración del taller sin necesidad de esperar una compra real:
1. Abre la aplicación en Expo Go.
2. Toca el botón **`🏦 Banco`** en la cabecera.
3. Se abrirá la pantalla **Automatización Bancaria**.
4. Puedes seleccionar presets (Bancolombia, Nequi, Nu, Davivienda) o escribir cualquier notificación de prueba.
5. Pulsa **Disparar Webhook Bancario**:
   - La aplicación invoca el backend FastAPI por Tailscale/LAN (`POST /webhooks/bank`).
   - El extractor LLM parsea los datos estructurados (Monto, Comercio, Medio de pago, Categoría).
   - Se guarda en PostgreSQL y se actualiza el monitor de transacciones en vivo.

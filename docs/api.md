# Especificación de API REST: Contratos de Endpoints y Seguridad

Este documento define la referencia completa de la API REST provista por el servidor **FastAPI**, sus contratos de datos, métodos de autenticación, esquemas de solicitud/respuesta y códigos de error.

---

## 1. Convenciones y Seguridad General

- **URL Base por Defecto**: `http://localhost:8000` (Local), `http://192.168.40.15:8000` (LAN), o `http://100.95.54.56:8000` (Tailscale).
- **Documentación Interactiva Swagger**: `http://<HOST>:8000/docs`
- **Documentación ReDoc**: `http://<HOST>:8000/redoc`
- **Esquema OpenAPI JSON**: `http://<HOST>:8000/openapi.json`
- **Doble Enrutamiento**: Todos los endpoints están disponibles tanto en la raíz (ej: `/chat`) como bajo el prefijo unificado `/api` (ej: `/api/chat`).

### Esquema de Autenticación
1. **Autenticación Bearer**:
   - Encabezado: `Authorization: Bearer <API_BEARER_TOKEN>` o alternativamente `X-API-Key: <API_BEARER_TOKEN>`.
   - Protege: `/chat`, `/voice`, `/tts`, `/db/status`, `/db/summary`, `/db/table/*`, `/webhooks/bank/recent`.
   - Si `API_BEARER_TOKEN` está vacío en `.env`, el servidor opera en modo de desarrollo permisivo con advertencia en consola. Si se define un token, cualquier petición sin dicho token será rechazada con `HTTP 401 Unauthorized`.
2. **Autenticación de Webhook Bancario**:
   - Encabezado: `X-Webhook-Secret: <BANK_WEBHOOK_SECRET>`.
   - Protege: `POST /webhooks/bank`.
   - Comprobación en tiempo constante con `secrets.compare_digest` para prevenir ataques de canal lateral por temporización.

---

## 2. Endpoints de Diagnóstico y Salud

### `GET /health`
Verifica la disponibilidad del proceso del backend.
- **Acceso**: Público (sin autenticación).
- **Respuesta Exitosa (200 OK)**:
```json
{
  "status": "healthy"
}
```

### `GET /db/status`
Verifica la conectividad activa con PostgreSQL en Supabase.
- **Seguridad**: Requiere Bearer Token.
- **Respuesta Exitosa (200 OK)**:
```json
{
  "status": "connected",
  "connected": true,
  "tables": [
    "users",
    "tasks",
    "emails",
    "financial_accounts",
    "credit_cards",
    "loans",
    "saving_goals",
    "transactions"
  ],
  "error": null,
  "timestamp": "2026-09-21T20:30:00.000Z"
}
```

### `GET /db/summary`
Retorna el conteo exacto de filas en cada una de las tablas del sistema.
- **Seguridad**: Requiere Bearer Token.
- **Respuesta Exitosa (200 OK)**:
```json
{
  "status": "connected",
  "counts": {
    "tasks": 12,
    "emails": 8,
    "financial_accounts": 3,
    "credit_cards": 2,
    "loans": 1,
    "saving_goals": 2,
    "transactions": 45,
    "reminders": 4,
    "tasks_only": 8
  },
  "timestamp": "2026-09-21T20:30:00.000Z"
}
```

---

## 3. Endpoints Conversacionales y de Voz

### `POST /chat`
Endpoint principal para interacción por texto con el orquestador multi-agente.
- **Seguridad**: Requiere Bearer Token.
- **Request Body**:
```json
{
  "message": "Anota comprar repuestos para el carro y dime cuánto dinero tengo disponible"
}
```
- **Validaciones**: Longitud de mensaje entre 1 y 4096 caracteres.
- **Respuesta Exitosa (200 OK)**:
```json
{
  "response": "Listo, anoté la tarea 'Comprar repuestos para el carro' y tu balance disponible es $3.500.000 COP.",
  "intent": "combined",
  "agent": "MultiAgent",
  "tools_executed": [
    "create_task",
    "calculate_cash_flow"
  ],
  "structured_intent": {
    "agent": "combined",
    "tool": null,
    "arguments": {},
    "actions": [
      {
        "agent": "secretary",
        "tool": "create_task",
        "arguments": {
          "title": "Comprar repuestos para el carro"
        }
      },
      {
        "agent": "financial",
        "tool": "calculate_cash_flow",
        "arguments": {
          "period": "current_month"
        }
      }
    ]
  },
  "audio_url": "/static/audio/tts/tts_a1b2c3d4.wav"
}
```

### `POST /voice`
Recepción de audio binario grabado en el móvil, transcripción STT con Whisper, orquestación y respuesta con síntesis TTS.
- **Seguridad**: Requiere Bearer Token.
- **Content-Type**: `multipart/form-data`.
- **Campos**:
  - `file`: Archivo binario de audio (`.m4a`, `.wav`, `.aac`, `.mp3`, `.ogg`, `.caf`).
- **Restricciones**: Máximo 25 MB. Nombres sanitizados en disco contra ataques de Path Traversal.
- **Respuesta Exitosa (200 OK)**:
```json
{
  "filename": "audio_recording.m4a",
  "transcribed_text": "¿Cuánto gasté hoy en alimentación?",
  "intent": "financial",
  "agent": "financial",
  "response": "Hoy has registrado un gasto de $45.000 COP en la categoría alimentación.",
  "tools_executed": [
    "calculate_cash_flow"
  ],
  "audio_url": "/static/audio/tts/tts_e5f6g7h8.wav"
}
```

### `POST /tts`
Sintetiza texto arbitrario a voz y genera un archivo de audio WAV en el servidor.
- **Seguridad**: Requiere Bearer Token.
- **Query Params**: `as_json` (`true` para recibir JSON con `audio_url`, `false` para descarga binaria directa).
- **Request Body**:
```json
{
  "text": "Tienes una tarea pendiente para mañana a las diez de la mañana.",
  "voice": "es"
}
```
- **Respuesta Exitosa (200 OK con `as_json=true`)**:
```json
{
  "status": "success",
  "audio_url": "/static/audio/tts/tts_12345678.wav",
  "text": "Tienes una tarea pendiente para mañana a las diez de la mañana."
}
```

### `GET /tts/{filename}`
Descarga o streaming del archivo de audio WAV generado por el motor TTS.
- **Seguridad**: Público / Restringido al directorio de audio. Protegido contra Path Traversal (`..`).
- **Respuesta**: Stream binario con cabecera `Content-Type: audio/wav`.

---

## 4. Endpoints de Webhooks Bancarios

### `POST /webhooks/bank`
Ingesta automática de notificaciones push bancarias enviadas por MacroDroid, Automate, Tasker o servicios externos.
- **Seguridad**: Requiere `X-Webhook-Secret`.
- **Request Body**:
```json
{
  "source": "Bancolombia",
  "content": "Bancolombia: Compra por $45.000 en Éxito Calle 80 con tarjeta terminada en 4321 el 21/09/2026 14:35.",
  "user_id": "a0000000-0000-0000-0000-000000000001"
}
```
- **Validaciones**: `source` y `content` obligatorios, `content` máximo 2000 caracteres, `user_id` en sintaxis UUID válida si se suministra.
- **Respuesta Exitosa (200 OK)**:
```json
{
  "status": "success",
  "message": "Transacción registrada exitosamente",
  "transaction_id": "b3c4d5e6-f7a8-4901-b2c3-d4e5f6a7b8c9",
  "extraction": {
    "amount": 45000.0,
    "currency": "COP",
    "merchant": "Éxito Calle 80",
    "type": "expense",
    "category": "groceries",
    "card_last_four": "4321",
    "account_mask": null,
    "payment_method": "credit_card",
    "notes": "Compra detectada automáticamente"
  }
}
```

### `GET /webhooks/bank/recent`
Consulta las últimas transacciones ingresadas mediante la vía de webhooks bancarios.
- **Seguridad**: Requiere Bearer Token.
- **Query Params**: `limit` (número entero entre 1 y 100, default 10).
- **Respuesta Exitosa (200 OK)**:
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "id": "b3c4d5e6-f7a8-4901-b2c3-d4e5f6a7b8c9",
      "amount": 45000.0,
      "currency": "COP",
      "category": "groceries",
      "merchant": "Éxito Calle 80",
      "type": "expense",
      "source": "webhook_bank",
      "transaction_date": "2026-09-21T19:35:00.000Z"
    }
  ]
}
```

---

## 5. Endpoints de Gestión Directa de Base de Datos (CRUD)

Permiten administración directa desde la aplicación móvil o paneles de integración externa sobre las tablas autorizadas (`tasks`, `reminders`, `transactions`, `financial_accounts`, `credit_cards`, `loans`, `saving_goals`, `emails`).

### `GET /db/table/{table_name}`
- **Parámetros de Consulta**:
  - `category`: Filtro opcional por categoría.
  - `status`: Filtro opcional por estado.
  - `limit`: Límite de registros (default 100, máximo 500).
- **Respuesta (200 OK)**: Retorna lista de objetos JSON ordenados cronológicamente descendente.

### `POST /db/table/{table_name}`
- **Cuerpo**: Objeto JSON con los campos de la entidad.
- **Comportamiento**: Inyecta automáticamente `id` (UUIDv4) y `user_id` (`DEFAULT_USER_ID`) si no se suministran, y valida valores permitidos.
- **Respuesta (200 OK)**: Retorna el registro insertado y su ID persistido.

### `PATCH /db/table/{table_name}/{record_id}`
- **Cuerpo**: Campos a modificar (excluyendo `id` y `user_id`).
- **Comportamiento**: Actualiza la fila en Supabase y actualiza `updated_at`. Si se marca una tarea como `completed`, asigna `completed_at = NOW()`.
- **Respuesta (200 OK)**: Retorna los datos actualizados.

### `DELETE /db/table/{table_name}/{record_id}`
- **Comportamiento**: Elimina de forma atómica la fila por su clave primaria UUID y sincroniza la memoria caché.
- **Respuesta (200 OK)**: `{"status": "deleted", "id": "<UUID>", "success": true}`.

---

## 6. Códigos de Estado y Manejo de Errores

| Código HTTP | Significado | Causa Frecuente |
| :--- | :--- | :--- |
| `200 OK` | Operación exitosa | Petición procesada y resuelta correctamente. |
| `400 Bad Request` | Petición inválida | Parámetros obligatorios ausentes, audio de 0 bytes o tabla no soportada. |
| `401 Unauthorized` | Autenticación denegada | Token Bearer o clave de API ausente o no coincidente. |
| `403 Forbidden` | Acceso prohibido | Secreto de webhook bancario (`X-Webhook-Secret`) inválido. |
| `404 Not Found` | No encontrado | Recurso o archivo de audio inexistente en disco. |
| `413 Payload Too Large` | Carga excesiva | Archivo de audio mayor a 25 MB o texto mayor a 4096 caracteres. |
| `500 Server Error` | Error interno | Excepción no controlada en cliente de base de datos o síntesis de voz. |

Todos los mensajes de error siguen el formato estándar:
```json
{
  "detail": "Descripción comprensible y exacta del error"
}
```
Esto permite al cliente móvil (`src/services/api.ts`) capturar y presentar la causa real del fallo en las alertas de usuario.

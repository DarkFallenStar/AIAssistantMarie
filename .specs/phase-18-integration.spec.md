# Specification Contract: Fase 18 — Integración Completa

## 1. Scope & Objectives
Formalizar la integración y unificación integral de todos los módulos desarrollados en el Asistente Personal Multi-Agente:
- **Flujo A (Conversacional y de Voz)**:
  - Mobile App (React Native / Expo SDK 57) captura voz (`expo-audio`) o texto.
  - Envía la petición a FastAPI Backend (`POST /voice` con multipart/form-data o `POST /chat` con JSON) con autenticación Bearer Token.
  - Backend ejecuta Speech-To-Text (STT) transcribiendo el audio en español.
  - Orquestador clasifica la intención mediante Function Calling / Structured Output y delega a los agentes especializados:
    - `SecretaryAgent`: tareas, recordatorios, correos electrónicos con confirmación humana.
    - `FinancialAgent`: transacciones, flujo de caja, tarjetas de crédito, préstamos, metas de ahorro.
    - `GeneralAgent`: conversación casual y preguntas generales.
  - Las herramientas de los agentes interactúan directamente con la Base de Datos PostgreSQL/Supabase (o fallback seguro en memoria).
  - El Orquestador sintetiza una respuesta profesional en lenguaje natural usando Failover LLM (Gemini 3.5 Flash / Ollama).
  - El servicio TTS sintetiza audio en formato WAV reproducible.
  - La Mobile App recibe la respuesta, muestra las burbujas en el chat y reproduce el audio automáticamente.

- **Flujo B (Ingestión de Notificaciones Bancarias)**:
  - Notificación bancaria (Push o SMS simulada en app o capturada vía MacroDroid en dispositivo físico).
  - Envío a `POST /webhooks/bank` con validación de secreto `X-Webhook-Secret`.
  - Extracción estructurada mediante LLM / heurística (comercio, monto, método, categoría).
  - Persistencia directa en la tabla `transactions` de la Base de Datos.
  - Sincronización con el Agente Financiero: las consultas posteriores por voz o chat al `FinancialAgent` reflejan inmediatamente las transacciones ingeridas vía webhook.

---

## 2. Interface & Endpoint Contracts

### Flujo A: Captura de Voz y Chat
- **Endpoint**: `POST /voice`
  - **Headers**:
    - `Authorization: Bearer <token>`
    - `Content-Type: multipart/form-data`
  - **Body**: `file`: binario de audio (`.m4a`, `.wav`, etc., <= 25MB).
  - **Response Schema (`VoiceUploadResponse`)**:
    ```json
    {
      "status": "success",
      "filename": "string",
      "size_bytes": 12345,
      "content_type": "audio/m4a",
      "transcribed_text": "string",
      "intent": "secretary" | "financial" | "general",
      "message": "string",
      "response": "string",
      "audio_url": "/static/audio/tts/tts_xxx.wav"
    }
    ```

- **Endpoint**: `POST /chat`
  - **Headers**:
    - `Authorization: Bearer <token>`
    - `Content-Type: application/json`
  - **Body**: `{"message": "string"}` (1 a 4096 caracteres)
  - **Response Schema (`ChatResponse`)**:
    ```json
    {
      "response": "string",
      "intent": "secretary" | "financial" | "general",
      "agent": "SecretaryAgent" | "FinancialAgent" | "GeneralAgent",
      "tools_executed": ["string"],
      "structured_intent": { ... } | null,
      "audio_url": "/static/audio/tts/tts_xxx.wav" | null
    }
    ```

### Flujo B: Webhook Bancario
- **Endpoint**: `POST /webhooks/bank`
  - **Headers**:
    - `X-Webhook-Secret: <secret>`
    - `Content-Type: application/json`
  - **Body**:
    ```json
    {
      "source": "android_notification_listener" | "macrodroid",
      "content": "Bancolombia le informa compra por $45.000 en Supermercado Metro...",
      "user_id": "a0000000-0000-0000-0000-000000000001"
    }
    ```
  - **Response Schema (`BankWebhookResponse`)**:
    ```json
    {
      "status": "success",
      "message": "Transacción bancaria procesada y registrada exitosamente.",
      "transaction_id": "uuid",
      "extracted": {
        "amount": 45000.0,
        "currency": "COP",
        "merchant": "Supermercado Metro",
        "type": "expense",
        "category": "supermercado",
        "payment_method": "tarjeta de credito"
      }
    }
    ```

---

## 3. Behavioral Scenarios (Gherkin)

### Scenario 1: Flujo Extremo a Extremo de Voz hacia el Agente Secretario
```gherkin
Given que el usuario graba un audio solicitando: "Anota una tarea urgente para revisar la presentación de mañana"
And la aplicación móvil envía el audio a POST /voice con autorización Bearer
When el backend procesa el archivo mediante STT y el Orquestador clasifica la intención como "secretary"
Then el SecretaryAgent ejecuta la herramienta "create_task"
And la tarea se persiste en la base de datos con prioridad "high" o título correspondiente
And el servicio TTS genera el archivo de audio de la respuesta
And la aplicación móvil recibe la transcripción, la respuesta textual y la URL del audio sintetizado.
```

### Scenario 2: Flujo Extremo a Extremo de Voz hacia el Agente Financiero
```gherkin
Given que el usuario graba un audio solicitando: "Registra un gasto de 35 dólares en combustible"
And la aplicación móvil envía el audio a POST /voice
When el backend transcribe el audio y el Orquestador clasifica la intención como "financial"
Then el FinancialAgent ejecuta la herramienta "create_transaction" con tipo "expense", monto 35.0 y categoría "transporte" o combustible
And el movimiento se almacena en la tabla de transacciones de la base de datos
And el Orquestador devuelve la confirmación del registro financiero junto con el audio TTS.
```

### Scenario 3: Flujo Paralelo de Notificación Bancaria y Consulta Inmediata en el Agente Financiero
```gherkin
Given que el sistema recibe una notificación bancaria por webhook en POST /webhooks/bank
And el payload contiene una compra de $89.900 en "Restaurante El Corral"
When el extractor procesa y guarda la transacción en la base de datos con source="webhook_bank"
And inmediatamente el usuario consulta al asistente por voz o chat: "¿Cuáles fueron mis últimas transacciones?"
Then el Orquestador delega la consulta al FinancialAgent
And el FinancialAgent consulta la base de datos mediante TransactionTools
And la respuesta incluye la compra de $89.900 en Restaurante El Corral procesada por el webhook.
```

### Scenario 4: Envío de Correo con Confirmación Humana en Pipeline Integrado
```gherkin
Given que el usuario solicita enviar un correo: "Envía un correo a supervisor@empresa.com con asunto Avance"
When el Orquestador identifica que send_email requiere confirmación humana (confirmed=False)
Then el sistema responde pidiendo confirmación al usuario sin despachar aún el email
When el usuario responde "Sí, confirmo el envío"
Then el Orquestador despacha el correo mediante MockEmailClient/ImapEmailClient
And el correo se persiste en la base de datos con estado "sent" o "unread".
```

### Scenario 5: Resiliencia de Seguridad y Failover en Pipeline Completo
```gherkin
Given que una petición a /voice o /chat no incluye token de autorización válido cuando la seguridad está activa
Then el backend responde inmediatamente con código HTTP 401 Unauthorized
And cuando una petición válida experimenta una falla en el LLM primario
Then el sistema conmuta automáticamente al proveedor secundario sin interrumpir la experiencia del usuario.
```

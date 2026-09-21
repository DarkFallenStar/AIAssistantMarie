# Specification Contract: Fase 19 — Suite Integral de Pruebas

## 1. Scope & Objectives
Implementar y formalizar la suite integral de pruebas para validar de extremo a extremo todos los subsistemas del Asistente Personal Multi-Agente:
- **Backend**:
  - `GET /health`: Comprobación de salud, versionado, latencia y respuesta JSON.
  - `POST /chat`: Validación de payloads, autenticación Bearer, validación de longitud (1 a 4096 caracteres) y estructura de respuesta.
  - `POST /webhooks/bank`: Autenticación `X-Webhook-Secret`, extracción estructurada de transacciones (monto, comercio, tipo, categoría), persistencia en base de datos y sincronización con endpoints de consulta.
- **Secretary Agent & Tools**:
  - `listar correos`: `list_emails` y `list_unread_emails`.
  - `buscar correo`: `search_emails` (con coincidencias y sin coincidencias), `get_email`, `summarize_email`.
  - `crear tarea`: `create_task` con título, fecha límite y prioridad.
  - `completar tarea`: `complete_task` con transición de estado y timestamp `completed_at`.
- **Financial Agent & Tools**:
  - `registrar transacción`: `create_transaction` con validación de tipo, categoría y monto.
  - `consultar transacciones`: `get_transactions` con filtrado por categoría y paginación.
  - `calcular flujo de caja`: `calculate_cash_flow` con saldo total líquido, ingresos, egresos y disponible neto.
  - `consultar metas`: `get_saving_goals` y `update_saving_goal` con cálculo de `progress_percentage`.
- **Orchestrator**:
  - `identificar Secretaría`: Clasificación heurística y Function Calling hacia `SecretaryAgent`.
  - `identificar Finanzas`: Clasificación heurística y Function Calling hacia `FinancialAgent`.
  - `combinar agentes cuando sea necesario`: Extensión para soportar consultas compuestas / multi-intención (ej. tarea + consulta financiera), ejecutando herramientas de múltiples agentes y sintetizando una respuesta combinada unificada.
- **Mobile**:
  - `permisos`: Verificación y solicitud de permisos nativos de audio (`AudioModule.requestRecordingPermissionsAsync`).
  - `grabación`: Ciclo de grabación (`prepareToRecordAsync`, `record`, `stop`) y máquina de estados (`IDLE` -> `RECORDING` -> `PROCESSING` -> `RESPONSE` -> `IDLE`).
  - `envío`: Envío de audio binario multipart (`sendAudioRecording`) y mensajes de texto JSON (`sendChatMessage`).
  - `respuesta`: Procesamiento de respuestas del asistente y renderizado de burbujas en el chat.
  - `TTS`: Limpieza de markdown (`stripMarkdownForTTS`) y reproducción de audio por voz (`Speech.speak`) con detención automática ante solapamiento (`Speech.stop`).
- **Tailscale**:
  - `conexión desde datos móviles`: Validación de binding `0.0.0.0`, resolución de IP Tailscale (`100.x.y.z`), conmutación de presets entre LAN y Tailscale en la app móvil, y tolerancia a latencia y reintentos.

---

## 2. Interface & Endpoint Contracts

### Backend Endpoints
1. `GET /health`
   - Response: `{"status": "ok", "app": "...", "version": "...", "server_time": "..."}` (HTTP 200)
2. `POST /chat`
   - Header: `Authorization: Bearer <token>`
   - Body: `{"message": "string"}` (1 a 4096 caracteres)
   - Response: `{"response": "string", "intent": "string", "agent": "string", "tools_executed": ["string"], "structured_intent": {...}}`
3. `POST /webhooks/bank`
   - Header: `X-Webhook-Secret: <secret>`
   - Body: `{"source": "string", "content": "string", "user_id": "uuid"}`
   - Response: `{"status": "success", "transaction_id": "uuid", "extracted": {...}}`

### Multi-Agent Orchestrator Contract
- Entrada compuesta: Consulta en lenguaje natural que involucra más de un dominio (ej. *"Anota una tarea de revisar el extracto mañana y dime cuánto dinero me queda en la cuenta"*).
- Salida combinada:
  - `agent`: `"MultiAgent"`
  - `intent`: `"combined"`
  - `tools_executed`: Contiene las herramientas de ambos agentes (ej. `["create_task", "calculate_cash_flow"]`).
  - `response`: Texto sintetizado por LLM abordando ambas partes de la consulta.

### Mobile Test Contracts
- Permisos: Retorna booleano `granted`. Si es falso, no inicia grabación y emite alerta.
- Grabación: Retorna URI local del archivo de audio grabado (`file://...`).
- Envío: `sendAudioRecording` genera `POST /voice` con `multipart/form-data`.
- Respuesta: Actualiza el estado de mensajes agregando el mensaje del usuario y la respuesta del asistente.
- TTS: `stripMarkdownForTTS(text)` elimina `**`, `*`, `#`, `` ` ``, `[]()` sin perder palabras; `Speech.speak` invocado con idioma `es-ES`.

---

## 3. Behavioral Scenarios (Gherkin)

### Scenario 1: Backend Health, Chat & Webhooks
```gherkin
Given que el backend está en ejecución
When se solicita GET /health
Then responde HTTP 200 con status "ok"
When se envía POST /chat con un mensaje válido y token Bearer
Then responde HTTP 200 con la respuesta del agente y tools ejecutadas
When se envía POST /webhooks/bank con una notificación bancaria y secreto válido
Then responde HTTP 200, extrae los datos de la compra y persiste la transacción.
```

### Scenario 2: Secretary Agent Flujo Completo
```gherkin
Given el agente SecretaryAgent
When se solicita listar correos
Then devuelve la lista de correos con su remitente y asunto
When se busca un correo por término clave
Then retorna únicamente los correos coincidentes
When se crea una tarea con título y prioridad
Then se registra con estado "pending"
When se marca la tarea como completada
Then su estado cambia a "completed" con timestamp válido.
```

### Scenario 3: Financial Agent Flujo Completo
```gherkin
Given el agente FinancialAgent
When se registra una transacción de gasto
Then se guarda con monto, tipo y categoría correcta
When se consultan las transacciones recientes
Then la lista incluye el registro recién creado
When se calcula el flujo de caja mensual
Then retorna el saldo líquido total y el balance neto
When se consultan las metas de ahorro
Then retorna el porcentaje de avance calculado contra el objetivo.
```

### Scenario 4: Orchestrator Multi-Agente Combinado
```gherkin
Given una consulta que combina acciones de secretaría y finanzas: "Anota una tarea de pagar el alquiler y dime cuánto saldo tengo"
When el Orchestrator procesa la entrada
Then identifica ambas intenciones
And ejecuta la herramienta de creación de tarea de SecretaryAgent
And ejecuta la herramienta de cálculo de flujo de caja de FinancialAgent
And sintetiza una respuesta unificada con agent="MultiAgent" y tools_executed conteniendo ambas herramientas.
```

### Scenario 5: Mobile Permisos, Grabación, Envío y TTS
```gherkin
Given el flujo móvil de captura y reproducción
When el usuario deniega el permiso de micrófono
Then la aplicación no inicia la grabación y notifica al usuario
When el permiso es otorgado y se presiona el micrófono
Then el grabador transiciona a RECORDING y luego a PROCESSING
When el audio se envía a POST /voice
Then se recibe la transcripción y respuesta, transicionando a RESPONSE
And el texto de respuesta se limpia de sintaxis markdown y se reproduce con Speech.speak.
```

### Scenario 6: Conexión Remota Tailscale
```gherkin
Given un dispositivo móvil conectado vía red móvil o remota
When se conmuta al preset de Tailscale (100.x.y.z:8000)
Then las peticiones GET /health y POST /chat se canalizan a través de la interfaz de red privada Tailscale
And el backend responde exitosamente sin requerir apertura de puertos en el router.
```

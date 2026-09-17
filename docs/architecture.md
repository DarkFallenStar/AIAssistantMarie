# Asistente Personal Inteligente Multi-Agente con Control por Voz
## Fase 0 — Documento de Arquitectura y Planificación

---

## 1. Arquitectura General

El sistema se basa en un modelo cliente-servidor desacoplado y seguro, diseñado para operar tanto en red local como de forma remota a través de una red mallada privada (Tailscale).

```
+-------------------------------------------------------------+
|                      DISPOSITIVO MÓVIL                      |
|  [ React Native + Expo (TypeScript) ]                       |
|   - Captura de audio (Micrófono)                            |
|   - Reproducción de respuestas (Audio/TTS)                  |
|   - Interfaz visual / Estado en tiempo real                 |
+-------------------------------------------------------------+
                              │
                              │ HTTPS / WSS vía Tailscale
                              ▼
+-------------------------------------------------------------+
|                     BACKEND / ORCHESTRATOR                  |
|  [ Python + FastAPI ]                                       |
|   - Router de Intenciones (LLM Orchestrator)                |
|   - Transcripción STT & Síntesis TTS                        |
|   - Gestor de Webhooks Bancarios                            |
|   - Conexión a Base de Datos                                |
+-------------------------------------------------------------+
           │                                │
           ▼                                ▼
+-----------------------+        +-----------------------+
|    SECRETARY AGENT    |        |    FINANCIAL AGENT    |
| - Gestión de Tareas   |        | - Registro de Gastos  |
| - Agenda & Recordat.  |        | - Balance & Reportes  |
| - Notas rápidas       |        | - Webhook Ingest      |
+-----------------------+        +-----------------------+
           │                                │
           +----------------+---------------+
                            │
                            ▼
+-------------------------------------------------------------+
|                   CAPA DE DATOS (DATABASE)                  |
|  [ Supabase / PostgreSQL ]                                  |
|   - Tablas: users, tasks, notes, transactions, categories   |
+-------------------------------------------------------------+
                            │
                            ▼
+-------------------------------------------------------------+
|                      PROVEEDOR DE LLM                       |
|  [ Ollama Local (Llama 3.2 / Qwen2.5) ]                     |
|  [ Alternativa: Google AI Studio API (Gemini 2.5/1.5) ]      |
+-------------------------------------------------------------+
```

---

## 2. Diagrama de Componentes

```mermaid
graph TD
    subgraph MobileApp ["Mobile App (React Native + TypeScript)"]
        UI["UI Visualizer & Chat"]
        AudioRec["Audio Recorder (STT Input)"]
        AudioPlay["Audio Player (TTS Output)"]
        NetClient["Network Client (Tailscale)"]
    end

    subgraph BackendAPI ["FastAPI Server"]
        Router["API Gateway & Webhook Endpoints"]
        STTService["STT Service (Whisper / Audio Model)"]
        TTSService["TTS Service (Fast Speech Engine)"]
        Orchestrator["LLM Orchestrator (Intent Classifier)"]
        SecAgent["Secretary Agent (Tools/Functions)"]
        FinAgent["Financial Agent (Tools/Functions)"]
    end

    subgraph LLMProviders ["LLM Providers"]
        Ollama["Ollama Local Engine"]
        Gemini["Google AI Studio API (Fallback/Cloud)"]
    end

    subgraph DatabaseLayer ["Supabase / PostgreSQL"]
        DBTasks["Tasks & Notes Tables"]
        DBFin["Transactions & Accounts Tables"]
        DBLogs["Audit & Memory Logs"]
    end

    subgraph External ["External Sources"]
        BankWebhook["Bank Webhook / SMS Alert"]
    end

    UI --> NetClient
    AudioRec --> NetClient
    NetClient --> Router
    Router --> AudioPlay
    BankWebhook --> Router

    Router --> STTService
    STTService --> Orchestrator
    Orchestrator --> SecAgent
    Orchestrator --> FinAgent

    SecAgent --> Ollama
    SecAgent --> Gemini
    FinAgent --> Ollama
    FinAgent --> Gemini

    SecAgent --> DBTasks
    FinAgent --> DBFin
    Orchestrator --> DBLogs

    SecAgent --> TTSService
    FinAgent --> TTSService
    TTSService --> Router
```

---

## 3. Flujo de Información

### Flujo A: Comando de Voz del Usuario
1. **Captura**: El usuario activa el micrófono en la app móvil. El flujo de audio se graba en formato estándar (PCM/WAV/M4A).
2. **Transporte**: La app envía el paquete de audio al backend FastAPI mediante HTTP POST multipart/stream vía la IP privada de **Tailscale**.
3. **Transcripción (STT)**: El backend convierte el audio a texto.
4. **Orquestación**:
   - El **Orchestrator** recibe el texto y analiza la intención utilizando el LLM (Ollama o Google AI Studio).
   - Clasifica la consulta para el **Secretary Agent** (ej. "recuérdame pagar la luz mañana") o el **Financial Agent** (ej. "¿cuánto gasté hoy?").
5. **Ejecución de Herramienta (Function Calling)**:
   - El agente seleccionado ejecuta las operaciones requeridas contra **Supabase / PostgreSQL** (consulta o inserción).
6. **Generación de Respuesta**: El agente redacta la respuesta en lenguaje natural.
7. **Síntesis (TTS)**: El texto de respuesta se convierte a audio.
8. **Retorno al Dispositivo**: El backend devuelve un payload con `{ text, audio_url/base64, metadata }`. La app reproduce el audio y actualiza la pantalla.

### Flujo B: Evento Bancario Automático (Webhook)
1. Un webhook externo (o servicio de notificación bancaria) envía un payload JSON a `POST /api/webhooks/bank`.
2. El backend autentica la firma o token secreto del webhook.
3. El **Financial Agent** normaliza el movimiento (monto, comercio, fecha), deduce la categoría mediante LLM y lo inserta en la base de datos de transacciones.
4. Si la app móvil está conectada, recibe la notificación o actualiza el balance.

---

## 4. Estructura de Carpetas Objetivo

```
project/
│
├── mobile/                        # Aplicación React Native (Expo SDK 57 + TS)
│   ├── assets/                    # Iconos, fuentes, audios de interfaz
│   ├── src/
│   │   ├── components/            # Visualizadores de onda de voz, tarjetas de balance
│   │   ├── screens/               # Pantalla de Asistente, Diagnóstico, Historial
│   │   ├── services/              # Cliente API, Audio Recorder, Audio Player
│   │   ├── config/                # URLs de entorno, constantes de red
│   │   └── types/                 # Interfaces TypeScript
│   ├── App.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                       # Servidor Python FastAPI
│   ├── app/
│   │   ├── api/                   # Endpoints (chat, voice, webhooks, health)
│   │   ├── core/                  # Configuración, seguridad, variables de entorno
│   │   ├── agents/                # Orquestador, Secretary Agent, Financial Agent
│   │   │   ├── orchestrator.py
│   │   │   ├── secretary.py
│   │   │   └── financial.py
│   │   ├── llm/                   # Adaptadores de LLM (Ollama Client, Gemini Client)
│   │   ├── audio/                 # Módulos STT y TTS
│   │   └── services/              # Lógica de negocio adicional
│   ├── requirements.txt
│   └── run.py
│
├── database/                      # Esquemas, migraciones y scripts SQL
│   ├── migrations/                # Scripts DDL para Supabase / PostgreSQL
│   ├── seeds/                     # Datos iniciales para pruebas
│   └── client.py                  # Cliente de conexión SQLAlchemy / Supabase
│
├── docs/                          # Documentación por fases y arquitectura
│   ├── architecture.md
│   ├── phase_0.md
│   └── api_specs.md
│
└── README.md
```

---

## 5. Tecnologías Utilizadas

| Capa | Tecnología | Justificación |
| :--- | :--- | :--- |
| **Frontend** | React Native + Expo SDK 57 + TypeScript | Rendimiento nativo fluido en Android/iOS, ecosistema de audio robusto y tipado estricto. |
| **Backend** | Python 3.13 + FastAPI + Uvicorn | Alta concurrencia asíncrona, integración nativa con ecosistemas de IA/LLM y validación de tipos Pydantic. |
| **Base de Datos** | Supabase (PostgreSQL 15+) | Base de datos relacional ACID completa, autenticación, API REST automática y WebSockets en tiempo real. |
| **LLM Primario** | Ollama (Llama 3.2 / Qwen 2.5) | Privacidad total, ejecución 100% local en máquina anfitriona sin costos de tokens. |
| **LLM Alternativo** | Google AI Studio API (Gemini 2.5 / 1.5) | Gran ventana de contexto, function calling nativo de ultra-baja latencia y fallback cloud sin fricción. |
| **Red** | Tailscale (WireGuard) | Comunicación cifrada punto a punto sin abrir puertos en el router, con IPs estáticas seguras (`100.x.y.z`). |

---

## 6. Dependencias Necesarias

### Backend (`backend/requirements.txt`)
- `fastapi>=0.115.0`: Framework web asíncrono.
- `uvicorn[standard]>=0.30.0`: Servidor ASGI de alto rendimiento.
- `pydantic>=2.8.0`, `pydantic-settings>=2.4.0`: Modelos de datos y configuración tipada.
- `httpx>=0.27.0`: Cliente HTTP asíncrono para llamadas a Ollama y APIs externas.
- `supabase>=2.7.0`: Cliente oficial de Supabase para Python.
- `sqlalchemy>=2.0.0`, `psycopg2-binary>=2.9.9`: ORM y driver nativo de PostgreSQL.
- `google-genai>=1.0.0` (o `google-generativeai`): SDK oficial de Google AI Studio.
- `python-dotenv>=1.0.0`: Carga de variables de entorno y secretos locales.

### Frontend (`mobile/package.json`)
- `expo`: SDK 57.
- `react`, `react-native`: Núcleo de componentes móviles.
- `expo-av` o `expo-audio`: Grabación y reproducción de audio nativo.
- `@react-native-async-storage/async-storage`: Persistencia de configuración en dispositivo.

---

## 7. Variables de Entorno Necesarias

### Backend (`backend/.env`)
```env
# Entorno y Red
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0

# Base de Datos (Supabase / PostgreSQL)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Proveedor LLM Principal (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Proveedor LLM Alternativo / Fallback (Google AI Studio)
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-2.0-flash

# Seguridad Webhook Bancario
BANK_WEBHOOK_SECRET=your_super_secret_signature_token
```

### Mobile (`mobile/.env` o `src/config/index.ts`)
```env
EXPO_PUBLIC_BACKEND_URL=http://100.x.y.z:8000   # IP Tailscale o IP LAN
```

---

## 8. Riesgos Técnicos y Mitigaciones

| Riesgo Técnico | Impacto | Estrategia de Mitigación |
| :--- | :--- | :--- |
| **Latencia de LLM Local en hardware modesto** | Alto (demoras en voz) | Utilizar modelos cuantizados ligeros (ej. `llama3.2:3b` o `qwen2.5:3b`); disponer del conector a Google AI Studio (Gemini Flash) con latencias < 500ms. |
| **Formatos de Audio incompatibles (Android/iOS ↔ Backend)** | Medio | Normalizar en la app a formato WAV PCM mono a 16kHz o MP4/AAC, universalmente compatibles. |
| **Pérdida de Conexión Tailscale** | Medio | Selector dinámico en la app móvil con reconexión automática entre LAN local y Tailscale IP. |
| **Fallo en Function Calling de modelos locales** | Alto | Esquemas JSON estrictos con validación Pydantic; si el JSON devuelto es inválido, reintentar con prompting correctivo estructurado. |

---

## 9. Orden Recomendado de Implementación

> **Principio de Diseño**: *"No construyas primero el asistente; construye primero el camino por el que viajará la información. Después añadimos la inteligencia encima de ese camino."*

1. **Fase 0 — Planificación (Actual)**:
   - Definición de arquitectura, diagrama de componentes, contratos de datos y mapa de ruta.
2. **Fase 1 — Estructura del Proyecto y Camino de Conectividad Base**:
   - Organizar las carpetas principales (`mobile`, `backend`, `database`, `docs`).
   - Servidor FastAPI base (`GET /api/health`).
   - App móvil conectando exitosamente al backend mediante IP de red / Tailscale.
3. **Fase 2 — Capa de Datos (Supabase / PostgreSQL)**:
   - Esquemas de tablas relacionales: tareas, notas, finanzas y transacciones.
   - Conexión del backend con Supabase y pruebas de migración/inserción.
4. **Fase 3 — Motor Multi-Agente y Orquestador (Texto primero)**:
   - Abstracción de LLM (Ollama + Google AI Studio).
   - Orquestador de intenciones.
   - Secretary Agent y Financial Agent ejecutando herramientas contra Supabase.
   - Chat de texto en la app móvil para validar el 100% de la lógica de negocio antes de introducir audio.
5. **Fase 4 — Canal de Voz Bidireccional (STT + TTS)**:
   - Captura de audio en la app y streaming/envío al backend.
   - Transcripción STT y síntesis TTS de respuesta en audio reproducido en la app móvil.
6. **Fase 5 — Webhook de Transacciones Bancarias**:
   - Endpoint autenticado para recibir transacciones bancarias.
   - Ingesta automática, categorización y actualización de balance.
7. **Fase 6 — Conectividad Tailscale y Despliegue**:
   - Validación del enlace seguro móvil fuera de la red local.

# Asistente Personal Inteligente Multi-Agente con Control por Voz

Asistente personal móvil basado en arquitectura multi-agente, control por voz (Speech To Text con Whisper), procesamiento de lenguaje natural desacoplado (Ollama / Google AI Studio Gemini), persistencia en Supabase (PostgreSQL), webhook bancario y conectividad privada mediante Tailscale.

---

## Arquitectura General

```
MOBILE APP (React Native + TypeScript + Expo SDK 57)
    │
    │ HTTPS / WebSocket (vía Red Local / Tailscale)
    ▼
BACKEND / ORCHESTRATOR (FastAPI)
    │
    ├────────────────────────┬────────────────────────┐
    ▼                        ▼                        ▼
SECRETARY AGENT       FINANCIAL AGENT           OTHER AGENTS...
    │                        │                        │
    └────────────────────────┴────────────────────────┘
                             │
                             ▼
                   DATABASE (PostgreSQL / Supabase)
                             │
                             ▼
                   LLM LAYER (Ollama / Gemini / Mock)
```

---

## Estructura del Proyecto

```
PersonalAssistantAI/
├── mobile/          # Código fuente y componentes de la aplicación móvil (Expo SDK 57)
├── backend/         # Servidor FastAPI (Orquestador, STT Whisper, Capa LLM, APIs)
│   ├── app/
│   │   ├── agents/      # Orquestador y agentes especializados
│   │   ├── api/         # Endpoints FastAPI (/chat, /voice, /health, /db)
│   │   ├── audio/       # Motor Speech To Text (Whisper)
│   │   ├── core/        # Configuración central (Settings, base de datos)
│   │   ├── schemas/     # Modelos de datos Pydantic
│   │   └── services/    # Capa de servicios LLM (Ollama, Gemini, Mock)
│   ├── tests/           # Suite de pruebas automatizadas
│   ├── run.py           # Script de inicio del servidor con uvicorn
│   └── requirements.txt # Dependencias de Python
├── database/        # Esquemas SQL, semillas y migraciones
├── docs/            # Documentación técnica de arquitectura
└── README.md
```

---

## Guía de Inicialización Paso a Paso

### 1. Requisitos Previos

- **Node.js** v18+ y npm instalados.
- **Python** v3.10+ instalado.
- Dispositivo móvil con la aplicación **Expo Go** instalada (disponible en Google Play Store).
- (Opcional) **Ollama** instalado localmente con modelo `llama3.2` O una clave gratuita de **Google AI Studio (Gemini)**.

---

### 2. Configurar y Levantar el Backend (FastAPI)

1. Abre una terminal en la carpeta `backend`:
   ```powershell
   cd backend
   ```

2. Crea y activa el entorno virtual de Python (si aún no lo tienes):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configura el archivo de variables de entorno `.env` en la carpeta `backend/`:
   ```env
   # Backend Environment Configuration
   ENVIRONMENT=development
   PORT=8000
   HOST=0.0.0.0

   # CORS
   CORS_ORIGINS=["*"]

   # Proveedor LLM: "google" | "ollama" | "mock"
   LLM_PROVIDER=google

   # Si usas Google AI Studio (Gemini):
   GEMINI_API_KEY=AIzaSyTuClaveAqui
   GEMINI_MODEL=gemini-2.0-flash

   # Si usas Ollama Local:
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2

   # Whisper STT
   WHISPER_MODEL_SIZE=tiny
   WHISPER_DEVICE=cpu
   WHISPER_COMPUTE_TYPE=int8
   ```

5. Inicia el servidor backend:
   ```powershell
   .venv\Scripts\python.exe run.py
   ```
   *El backend quedará escuchando en `http://0.0.0.0:8000` con recarga automática en caliente (`reload=True`).*

---

### 3. Configurar y Levantar la Aplicación Móvil (Expo)

1. Abre una segunda terminal en la raíz del proyecto (`PersonalAssistantAI`):
   ```powershell
   cd "PersonalAssistantAI"
   ```

2. Instala las dependencias de Node.js:
   ```powershell
   npm install
   ```

3. Configura la dirección IP de tu computadora para que tu móvil pueda conectarse:
   - Abre `mobile/src/config/index.ts` (o `src/config/index.ts`).
   - Define tu IP local (o tu IP de Tailscale):
     ```typescript
     export const DEFAULT_LAN_IP = "192.168.1.137"; // Cambia por la IP de tu PC
     export const DEFAULT_PORT = "8000";
     export const DEFAULT_BACKEND_URL = `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;
     ```

4. Inicia el servidor de desarrollo de Expo:
   ```powershell
   npx expo start
   ```

5. **Abrir en tu teléfono**:
   - Abre la app **Expo Go** en tu Android.
   - Escanea el código QR que aparece en la terminal.
   - ¡La aplicación compilará y se abrirá directamente en tu celular!

---

### 4. Verificación y Pruebas Automatizadas

Puedes ejecutar la suite completa de pruebas unitarias e integración en el backend:

```powershell
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests
```

*Verifica endpoints de salud, conexión a base de datos, captura de voz y Speech-to-Text (Whisper), capa LLM y fallback de orquestador.*

# Asistente Personal Inteligente Multi-Agente con Control por Voz

Asistente personal móvil basado en arquitectura multi-agente, control por voz, persistencia en Supabase (PostgreSQL), webhook bancario y conectividad privada mediante Tailscale.

## Arquitectura General

```
MOBILE APP (React Native + TypeScript)
    │
    │ HTTPS / WebSocket
    │
TAILSCALE
    │
    ▼
BACKEND / ORCHESTRATOR (FastAPI)
    │
    +--------------------+
    │                    │
    ▼                    ▼
SECRETARY AGENT      FINANCIAL AGENT
    │                    │
    +---------+----------+
              │
              ▼
    DATABASE (Supabase / PostgreSQL)
              │
              ▼
    LLM (Ollama / Google AI Studio)
```

## Estructura del Proyecto

```
project/
│
├── mobile/      # Aplicación móvil Expo SDK 57 (TypeScript)
├── backend/     # Servidor Python FastAPI (Agentes, STT/TTS, Webhook)
├── database/    # Esquemas SQL, migraciones y configuración Supabase
├── docs/        # Documentación de arquitectura y especificaciones
└── README.md
```

Consulta el documento completo en [docs/architecture.md](docs/architecture.md).

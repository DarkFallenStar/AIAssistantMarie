# Spec Contract: Fase 21 — Documentación Integral del Sistema

## 1. Scope & System Topology

### Problem & Objective
Consolidate, standardize, and produce comprehensive documentation for the Personal Assistant AI project, reflecting the complete 20-phase architecture and implementation across:
1. `README.md`: Central entry point for onboarding, configuration, operation, testing, and troubleshooting.
2. `docs/architecture.md`: Full architectural breakdown, component topology, sequence diagrams, and information flow.
3. `docs/database.md`: Supabase PostgreSQL relational schema, data dictionary, Entity-Relationship (ER) diagram, and persistence strategy.
4. `docs/api.md`: FastAPI REST endpoints, contracts, authentication, error handling, and payload models.
5. `docs/agents.md`: Multi-agent orchestration, intent classification, sub-agent capabilities, and tools catalog.
6. `docs/deployment.md`: Operational guide for local environments, Tailscale VPN networking, and mobile client execution.

### Architectural Visual Artifacts Required
1. **Architecture Diagram (Mermaid)**: Mobile (React Native / Expo), Network Gateway (Tailscale / LAN), Backend (FastAPI / Orchestrator), Specialized Sub-Agents, Tools, Database (Supabase PostgreSQL), and Dual LLM Engine (Gemini / Ollama).
2. **Sequence Diagrams (Mermaid)**:
   - Voice conversational pipeline: Audio Capture -> Whisper STT -> Orchestrator -> Sub-Agent -> Tool -> Database -> TTS Synthesis -> Mobile Player.
   - Bank automation pipeline: Push Notification -> Interception (MacroDroid) -> Webhook POST -> Structured Output Extraction -> Database Ingestion -> Financial Agent synchronization.
3. **Entity-Relationship (ER) Diagram (Mermaid)**: Full relational topology for `users`, `tasks`, `emails`, `financial_accounts`, `credit_cards`, `loans`, `saving_goals`, and `transactions`.

---

## 2. Document Specifications & Contracts

### A. `README.md`
Must strictly contain all the following structured sections:
1. **Descripción**: Project mission, core capabilities (voice, multi-agent, finance, secretary, bank automation, private mesh).
2. **Arquitectura**: High-level text and ASCII/Mermaid diagram.
3. **Requisitos**: Prerequisites (Node 18+, Python 3.10+, Expo Go on Android, Supabase project, Tailscale, Ollama/Gemini API key).
4. **Instalación**: Complete step-by-step setup for backend virtualenv and mobile packages.
5. **Configuración**: Directory layout and project setup.
6. **Variables de Entorno**: Complete dictionary of `.env` variables with defaults, types, and security guidelines.
7. **Ejecución del Backend**: Exact CLI commands (`backend/run.py`), ports, and hot-reload behavior.
8. **Ejecución de React Native**: Exact CLI commands (`npx expo start`), QR scanning on Android Expo Go, IP configuration.
9. **Configuración de Supabase**: PostgreSQL project creation, running `schema.sql` and `seeds.sql`, environment keys, in-memory fallback.
10. **Configuración de Ollama/Google AI**: Dual failover setup, model configurations, latency parameters, API keys.
11. **Configuración de Tailscale**: WireGuard overlay configuration, IP binding (`0.0.0.0`), mobile 1-tap switching.
12. **Configuración de Automatización Bancaria**: MacroDroid setup on Android, webhook configuration, `X-Webhook-Secret`, in-app simulator.
13. **Pruebas**: Running backend test suite (`unittest discover`), mobile test suite (`node --test`), and 12 MVP acceptance tests.
14. **Solución de Problemas**: Known gotchas, zombie process termination on Windows, UTF-8/cp1252 console encoding, UUID constraints, Gemini 503 fallback.

### B. `docs/architecture.md`
Must provide:
- System overview and design principles (Separation of concerns, offline resilience, Spec-Driven Development).
- Full Mermaid Architecture Diagram.
- Subsystem descriptions: Mobile Client, API Gateway, Orchestrator Layer, Sub-Agents, Tool Dispatcher, Database Layer, LLM Layer, TTS/STT Engines.
- Full Mermaid Sequence Diagrams for both voice interaction and webhook ingestion.

### C. `docs/database.md`
Must provide:
- PostgreSQL / Supabase architecture and ACID compliance.
- Complete Mermaid Entity-Relationship Diagram (`erDiagram`).
- Detailed data dictionary for every table: `users`, `tasks`, `emails`, `financial_accounts`, `credit_cards`, `loans`, `saving_goals`, `transactions`.
- Triggers, indexes, and constraints (`CHECK`, foreign keys with `ON DELETE CASCADE / SET NULL`).
- Hybrid persistence & mock fallback lifecycle.
- Direct CRUD endpoints and tabbed database management.

### D. `docs/api.md`
Must provide:
- API design conventions (RESTful, OpenAPI/Swagger at `/docs`).
- Authentication mechanisms (`Bearer` token, `X-API-Key`, `X-Webhook-Secret`).
- Detailed endpoint documentation:
  - System: `GET /`, `GET /health`
  - Assistant Chat: `POST /chat`
  - Voice & Speech: `POST /voice`, `POST /tts`, `GET /tts/{filename}`
  - Bank Ingestion: `POST /webhooks/bank`, `GET /webhooks/bank/recent`
  - Database Management: `GET /db/status`, `GET /db/summary`, `GET /db/table/{name}`, `POST /db/table/{name}`, `PATCH /db/table/{name}/{id}`, `DELETE /db/table/{name}/{id}`
- Request/Response JSON schemas and HTTP status codes.

### E. `docs/agents.md`
Must provide:
- Multi-Agent Orchestration architecture and execution flow.
- `OrchestratorService`: Intent classification algorithm, compound multi-agent pipeline (`agent: "combined"`, `actions: [...]`), heuristic routing vs LLM prompt.
- `SecretaryAgent`: Capabilities, task CRUD, priority matching, title search, reminders, email drafting and human-in-the-loop confirmation.
- `FinancialAgent`: Capabilities, cash flow calculations, expense/income analysis, accounts, credit cards, loans, saving goals, strict DB grounding, Colombian Peso (COP) support.
- `GeneralAgent`: Conversational greeting and general queries.
- `ToolDispatcher`: Dynamic tool execution and catalog.
- `FailoverLLMService`: Dual-provider architecture, latency profiles, error recovery.

### F. `docs/deployment.md`
Must provide:
- Local development deployment workflow.
- Windows host environment setup (Python 3.10+, PowerShell, virtualenv).
- Tailscale deployment: mesh topology, zero port-forwarding, Android integration.
- Supabase cloud deployment: SQL script execution, service keys, RLS.
- Mobile client execution: Expo Go workflow vs native APK builds (EAS Build).
- Production hardening checklist: Bearer tokens, webhook secrets, rate limiting, logging, process supervision.

---

## 3. Acceptance Criteria & Scenarios (Gherkin Syntax)

### Scenario 1: Comprehensive README Documentation
- **Given** a new developer or user clones the repository
- **When** they inspect `README.md`
- **Then** it must contain all 14 mandatory sections with exact setup commands, environment variables, Supabase instructions, Tailscale setup, and troubleshooting recipes.

### Scenario 2: Technical Architecture & Sequence Diagrams
- **Given** a developer reviews system flow in `docs/architecture.md`
- **When** they view the document
- **Then** it must render valid Mermaid diagrams for overall architecture, conversational sequence flow, and bank notification ingestion flow without syntax errors.

### Scenario 3: Database Entity-Relationship Specification
- **Given** a developer inspects `docs/database.md`
- **When** they examine the data model
- **Then** it must render a valid Mermaid `erDiagram` showing all 8 tables and relationships, and document each field, type, and constraint matching `database/schema.sql`.

### Scenario 4: API Contract Specification
- **Given** an API consumer integrates with FastAPI backend
- **When** they review `docs/api.md`
- **Then** every active route (`/health`, `/chat`, `/voice`, `/tts`, `/webhooks/bank`, `/db/*`) must be documented with parameters, authentication headers, request bodies, and response schemas.

### Scenario 5: Multi-Agent System Specification
- **Given** an engineer inspects agent capabilities in `docs/agents.md`
- **When** they review `SecretaryAgent`, `FinancialAgent`, and `OrchestratorService`
- **Then** all tools, intent schemas, compound intent decomposition, and human-in-the-loop workflows must be documented.

---

## 4. Impacted Components
- `README.md` [MODIFY]
- `docs/architecture.md` [MODIFY]
- `docs/database.md` [NEW]
- `docs/api.md` [NEW]
- `docs/agents.md` [NEW]
- `docs/deployment.md` [NEW]
- `.specs/phase-21-documentation.spec.md` [NEW]

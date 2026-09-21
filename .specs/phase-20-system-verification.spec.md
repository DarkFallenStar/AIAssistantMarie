# Spec Contract: End-to-End System Verification Playbook

## 1. Scope & System Topology

### Problem & Objective
Provide an exhaustive, executable specification and verification protocol to validate the complete Personal Assistant AI application across all 19 implemented phases, covering:
- Frontend Mobile Client (React Native / Expo SDK 57 on Android)
- Backend Orchestrator (FastAPI / Asynchronous Python)
- Dual LLM Engine (Google AI Studio Gemini + Ollama with Bidirectional Failover)
- Database Persistence (Supabase PostgreSQL + Resilient Mock Fallback)
- Voice Input (Whisper STT) & Audio Response (TTS WAV synthesis)
- Bank Notification Ingestion & Automation (MacroDroid / In-App Simulator)
- Network Mesh (Tailscale WireGuard overlay + Local LAN)
- Defense-in-Depth Security (Bearer Token, Webhook Secret, Sanitization)

### System Architecture Reference
```
[Android Mobile / Expo Go]
       │
       ├─── (LAN Wi-Fi: 192.168.40.15:8000)
       └─── (Tailscale VPN: 100.95.54.56:8000)
                 │
                 ▼
       [FastAPI Backend :8000]
                 │
                 ├── Auth Gate (Bearer / Webhook Secret)
                 ├── Audio STT (Whisper tiny / int8)
                 ├── Audio TTS (WAV streaming)
                 │
                 ▼
       [Orchestrator Service]
        ├── Intent Classifier (LLM Structured / Heuristic)
        │
        ├── Secretary Agent ───► TaskTools, EmailTools, ReminderTools
        │
        ├── Financial Agent ───► TransactionTools, CashFlowTools,
        │                        CreditCardTools, LoanTools, SavingGoalTools
        │
        └── Compound Multi-Agent Pipeline (Sequential execution across agents)
                 │
                 ▼
       [Storage & Persistence]
        ├── Supabase PostgreSQL (Live cloud tables with UUID primary keys)
        └── In-Memory Fallback Repositories (Deterministic offline resilience)
```

---

## 2. Phase-by-Phase Verification Matrix

| Phase | Subsystem | Verification Goal | Automated Test | Manual Test Target |
|---|---|---|---|---|
| **Fase 1-5** | Mobile UI & Core | React Native layout, Safe Area, Keyboard avoiding | `test_mobile_assistant.test.mjs` | Expo Go UI rendering & keyboard input |
| **Fase 6** | Speech-to-Text | Whisper audio ingestion & transcription | `test_stt.py` | Mic button audio recording in mobile |
| **Fase 7** | LLM Engine | Gemini & Ollama integration with failover | `test_llm.py` | Chat prompt response generation |
| **Fase 8** | Orchestrator | Heuristic classification & fallback | `test_orchestrator_tools.py` | Multi-domain prompt routing |
| **Fase 9** | Secretary Agent | Tasks, emails, reminders management | `test_secretary_agent.py` | "Crea una tarea urgente...", "Recuérdame..." |
| **Fase 10** | Financial Agent | Balances, loans, cards, cash flow | `test_financial_agent.py` | "Cuánto dinero me queda?", "Mis tarjetas" |
| **Fase 11** | Function Calling | StructuredIntent JSON extraction & execution | `test_function_calling.py` | Parametric tool calls via LLM |
| **Fase 12** | Email & HITL | Draft creation & human confirmation gate | `test_email_phase12.py` | "Envía un correo..." -> "Sí, confirmo" |
| **Fase 13** | TTS Voice Response | WAV audio synthesis & playback | `test_tts.py` | Audio playback on mobile response |
| **Fase 14** | Bank Webhooks | Bank push extraction & transaction recording | `test_bank_webhook.py` | `POST /webhooks/bank` |
| **Fase 15** | Notification Sim | MacroDroid instructions & in-app simulator | `NotificationAutomationScreen.tsx` | Simulator screen preset buttons |
| **Fase 16** | Tailscale Remote | Zero-port-forwarding WireGuard access | `test_fase19_tailscale.py` | Diagnostic screen Tailscale toggle |
| **Fase 17** | Security Hardening | Bearer token & webhook secret verification | `test_security.py` | Header authorization validation |
| **Fase 18** | Full Integration | End-to-end unified module orchestration | `test_phase18_integration.py` | Ingest bank webhook -> query balance |
| **Fase 19** | Testing & Multi-Agent | Compound intents & complete mobile tests | `test_fase19_*.py` + `test_mobile_assistant` | Single query with reminder + expense |

---

## 3. Pre-Flight Checklist Before Full Execution

Before launching live end-to-end tests with the mobile device, verify the following:

1. **Host Network Addresses**:
   - Wi-Fi LAN IP: `192.168.40.15`
   - Tailscale IP: `100.95.54.56`
   - Target Port: `8000`
2. **Environment Files**:
   - Root `.env` and `backend/.env` configured.
   - `LLM_PROVIDER=dual` with `GEMINI_API_KEY` or `LLM_PROVIDER=google` or `mock`.
   - `API_BEARER_TOKEN` and `BANK_WEBHOOK_SECRET` aligned between backend and mobile config.
3. **Port Hygiene**:
   - Port 8000 free of orphan Python/uvicorn processes.
   - Port 8081 free for Metro/Expo bundler.
4. **Client-Backend Schema Parity**:
   - `src/` and `mobile/src/` synchronized (verified identical).

---

## 4. Operational Run Commands

### A. Backend Execution
```powershell
# From workspace root:
& "backend/.venv/Scripts/python.exe" backend/run.py
```
*Expected log output:*
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### B. Mobile Client Execution
```powershell
# In a second terminal (workspace root):
npx expo start
```
*Action: Scan QR code with Expo Go on Android phone.*

### C. Automated Test Suites
```powershell
# Backend (166 tests):
cd backend
& ".venv/Scripts/python.exe" -m unittest discover -s tests -p "test_*.py" -v

# Mobile (10 tests):
node --test tests/mobile/test_mobile_assistant.test.mjs
```

---

## 5. End-to-End Acceptance Scenarios (Gherkin Format)

### Scenario 1: Connectivity & Diagnostic Verification
```gherkin
Given the backend is running on http://0.0.0.0:8000
When the user opens the mobile app and taps "Diagnóstico de Red"
Then the diagnostic screen tests:
  1. Backend liveness (GET /health) -> Status OK (Green)
  2. Database status (GET /db/status) -> Status OK (Green)
  3. LLM Orchestrator (POST /chat) -> Echo response OK (Green)
And the user can switch between "LAN Wi-Fi" and "Tailscale" with 1 tap.
```

### Scenario 2: Secretary Agent Reminder & Task
```gherkin
Given the user is on the Assistant Screen
When the user speaks or types: "Anota una tarea urgente para entregar el reporte mañana"
Then the Orchestrator identifies intent "create_task" for SecretaryAgent
And the task is persisted in the database with high priority
And the assistant responds with a confirmation message and synthesizes speech.
```

### Scenario 3: Human-in-the-Loop Email Dispatch
```gherkin
Given the user requests: "Envía un correo a profesor@universidad.edu con asunto Tesis"
When the SecretaryAgent processes the request
Then the assistant creates a draft and responds: "He preparado el borrador... ¿Deseas confirmarlo?"
And requires_confirmation is set to True
When the user replies: "Sí, confirmo el envío"
Then the email tool executes dispatch and confirms sending to the user.
```

### Scenario 4: Bank Ingestion via Webhook & Financial Reflection
```gherkin
Given the user opens "Centro de Automatización Bancaria"
When the user taps the simulation button "Bancolombia ($45.000 COP)"
Then a POST /webhooks/bank request is dispatched with valid authorization
And the transaction is extracted and stored in PostgreSQL
When the user returns to the Assistant Screen and asks: "¿Cuáles fueron mis últimos gastos?"
Then the FinancialAgent lists the newly ingested transaction.
```

### Scenario 5: Compound Multi-Agent Request
```gherkin
Given the user submits: "Anota comprar repuestos para el carro y dime cuánto dinero tengo disponible"
When the Orchestrator evaluates the query
Then it identifies a compound multi-agent intent:
  - Action 1: SecretaryAgent creates task "comprar repuestos para el carro"
  - Action 2: FinancialAgent computes cash flow / liquid balance
And the system synthesizes a unified, coherent response containing both outcomes.
```

---

## 6. Known Edge Cases & Operational Gotchas

1. **Expo Go File Uploads**:
   Always use `expo-file-system` `new File(audioUri).upload(...)` instead of React Native `{ uri, name, type }` FormData shorthand.
2. **Windows stdout Charset**:
   Windows console uses cp1252. No unencoded emojis in `print()` statements.
3. **Database UUID Syntax**:
   Never query `.eq("id", ...)` with non-UUID strings to avoid PostgreSQL `22P02`.
4. **Tailscale Remote Operation**:
   When using Tailscale, ensure both PC and mobile device have Tailscale active under the same Tailnet.

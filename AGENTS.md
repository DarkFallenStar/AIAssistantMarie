# Project Guidelines & Architecture: Multi-Agent Personal Assistant

## Expo Documentation Rule
Read the exact versioned docs at https://docs.expo.dev/versions/v57.0.0/ before writing any mobile code.

---

## 1. Core Workflow Directives
- **Phased & Progressive Development**: DO NOT attempt to build the entire project all at once. Build strictly phase-by-phase. Each phase MUST be fully functional and verified before proceeding to the next.
- **No Automatic Phase Advancement**: DO NOT automatically advance to the next phase until the current phase is fully working, verified, and explicitly approved by the user.
- **Spec-Driven & Persistent Context**: Every phase and component must adhere to the Spec-Driven Development (SDD) contract before code is written. In EVERY session, whenever an architectural decision, error, gotcha, or learning is discovered, it MUST be recorded into:
  1. Codebase-memory ADR via `manage_adr` tool.
  2. Codebase-memory graph via `index_repository(persistence=True)`.
  3. `AGENTS.md` and active `.specs/`.
  This guarantees that ANY future conversation automatically retains all context and learnings.
- **Mandatory Phase Completion Response Format**:
  Upon finishing ANY phase, the final response MUST follow this exact structure:

  ## Fase completada
  Qué se hizo.

  ## Archivos
  Lista de archivos creados/modificados.

  ## Cómo ejecutar
  Comandos necesarios.

  ## Cómo probar
  Pasos concretos para verificarlo.

  ## Problemas conocidos
  Errores o limitaciones actuales.

  ## Siguiente fase
  Indicar qué se implementará después.

- **Responsive UI & Keyboard Ergonomics**: All mobile screens and components MUST be fully responsive across various device sizes. The virtual keyboard MUST properly displace the screen so that input bars, send buttons, and conversation contents are never hidden or obscured when the keyboard is open.
- **Mandatory App Testing Instructions in Phase Reports**: In EVERY phase completion report / walkthrough, ALWAYS provide explicit, step-by-step instructions explaining exactly how the user can test and experience the newly implemented features directly from the mobile application (Expo Go) and/or backend endpoints.
- **Mandatory Git Synchronization per Phase**: Upon completing ANY phase (and before submitting the final phase completion report), ALL changes (code, tests, specs, and docs) MUST be staged (`git add .`), committed with a clear semantic message (e.g., `feat(fase-X): ...`), and pushed to GitHub (`git push`).


---

## 2. System Architecture & Topology

```
MOBILE APP (Android via Expo Go)
    │
    │ HTTPS / WebSocket (via Tailscale)
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
                   LLM LAYER (Local Ollama / Extensible)
```

---

## 3. Technology Stack & Constraints
1. **Backend**: FastAPI (Python), asynchronous and modular.
2. **LLM Engine**: Local model via Ollama, built with a provider-agnostic abstraction layer so additional local or cloud LLMs can be seamlessly integrated.
3. **Mobile Client**: React Native with Expo (tested on Android via Expo Go).
4. **Networking**: Secured private connectivity via Tailscale.
5. **Database**: PostgreSQL / Supabase.
   - Core Entities: `users`, `tasks`, `emails`, `financial_accounts`, `credit_cards`, `loans`, `saving_goals`, `transactions`.
6. **Key Capabilities**:
   - Voice input capture & STT.
   - Orchestration & multi-agent routing (Secretary vs Financial).
   - Tool/Function calling.
   - TTS (Text-to-Speech) audio response.
   - Bank transaction webhook ingestion.

---

## 4. Strict Zero-Regression Guidelines (Learned Gotchas)

### A. Mobile (Expo SDK 57 & React Native 0.86+)
1. **SafeAreaView**: NEVER import `SafeAreaView` from `'react-native'` (deprecated). ALWAYS import from `'react-native-safe-area-context'` and ensure root is wrapped in `<SafeAreaProvider>`.
2. **File & Audio Uploads**: NEVER use legacy React Native `{ uri, name, type }` object shorthand in `FormData.append()` (fails with `Unsupported FormDataPart implementation` in WinterCG / Hermes). ALWAYS use `expo-file-system`'s `new File(audioUri).upload(url, { uploadType: UploadType.MULTIPART, fieldName: 'file' })`.
3. **Audio Capture**: NEVER use deprecated `expo-av` for recording. ALWAYS use `expo-audio` (`useAudioRecorder`, `RecordingPresets.HIGH_QUALITY`, `AudioModule`, `setAudioModeAsync`).
4. **Keyboard Ergonomics**: ALWAYS configure `KeyboardAvoidingView` with `behavior={Platform.OS === 'ios' ? 'padding' : 'height'}` and appropriate offset (`20`). ALWAYS add `keyboardShouldPersistTaps="handled"` on scrollable lists and dismiss keyboard when tapping outside.

### B. Backend (FastAPI & Windows Environment)
1. **Windows Console Encoding**: NEVER write emojis or raw UTF-8 symbols in `print()` statements destined for Windows stdout (causes `UnicodeEncodeError: 'charmap' codec can't encode characters` in cp1252). Use ASCII tags like `[VOICE]`, `[API]`, `[DB]`.
2. **Multipart Uploads**: ALWAYS ensure `python-multipart` is listed in requirements and installed in `.venv` for any file upload endpoint.
3. **Auto-reload in Development**: ALWAYS invoke `uvicorn.run("app.main:app", ..., reload=True)` passing the import string so file modifications take effect immediately without orphan processes or port collisions.
4. **Orphan Processes & Socket Collision on Windows**: If backend requests do not appear in console logs, ALWAYS check `netstat -ano | findstr :8000`. Windows allows ghost/zombie Python instances to retain bound sockets in `CLOSE_WAIT` or dual-LISTEN, hijacking incoming packets from mobile clients without forwarding them to the active terminal process. Kill dangling PIDs using `Stop-Process -Id <PID> -Force`.

### C. LLM & Connectivity (Learned Gotchas)
1. **Dual Simultaneous Providers & Automatic Bidirectional Failover**:
   - `FailoverLLMService` wraps both Google Gemini and local Ollama (`llama3.2`).
   - If the primary provider fails (timeout, HTTP error, network unreachable, rate limit), it automatically logs `[LLM-FAILOVER]` and seamlessly executes on the secondary provider, and vice-versa.
2. **Google AI Studio Model Selection & Latency Profile**:
   - `gemini-3.5-flash` is the recommended production model for fast, high-quality responses (consistent 2.5s - 4.5s response time without 503 high-demand spikes).
   - `gemini-3.8-flash` is currently in preview and periodically returns HTTP 503 ("This model is currently experiencing high demand").
   - `gemini-3.6-flash` is functional but has higher latency (10s - 22s).
3. **LLM Timeout Configuration**:
   - `GoogleAIService` timeout MUST NOT be hardcoded to short intervals (e.g. 12s was causing false timeout aborts). It now defaults to `GEMINI_TIMEOUT_SECONDS=25.0s`.
   - `mobile/src/services/api.ts` maintains a timeout of `35000ms` (35s) so multi-step tool execution and dual failover have sufficient time to finish.
4. **Instant Graceful Degradation**:
   - If both LLM providers fail or are disconnected, agents MUST degrade gracefully and return structured tool responses immediately rather than timing out.

### D. Database & Tool Contracts (Supabase / PostgreSQL)
1. **UUID Columns**: In PostgreSQL, tables (`tasks`, `emails`, `users`) define `id UUID PRIMARY KEY`. NEVER insert arbitrary string prefixes (like `t-12345` or `draft-12345`). ALWAYS use valid standard UUIDs (`str(uuid.uuid4())`).
2. **Column Naming**: Verify active SQL schemas before crafting queries (e.g. `financial_accounts.account_name`, not `name`).
3. **Seed & In-Memory Synchronization**: Tools must combine or fall back seamlessly between live Supabase records and in-memory mock repositories so unit tests and offline workflows remain 100% deterministic.
4. **UUID Query Protection**: Before executing `.eq("id", target_id)` against Supabase tables, tools MUST validate with `is_valid_uuid(target_id)`. Non-UUID identifiers (such as mock or natural language references) must skip database UUID queries and match in-memory to prevent PostgreSQL error `22P02: invalid input syntax for type uuid`.
5. **Table Check Constraints & Draft Resilience**: PostgreSQL enforces table-level CHECK constraints (e.g., `emails.status IN ('unread', 'read', 'archived', 'starred', 'spam')`). When tools perform inserts that may conflict with active constraints (e.g., creating draft emails), they must implement resilient fallback logic (e.g., saving with `status='unread'` and prefixing `[Borrador]`) to guarantee persistence without unhandled exceptions.
6. **Foreign Key Integrity**: Tables with foreign keys (such as `tasks.user_id` or `emails.user_id`) require existing user records. Tools must default to `DEFAULT_USER_ID` (`a0000000-0000-0000-0000-000000000001` seeded in Phase 3) when `user_id` is omitted.
7. **Financial Grounding & Anti-Hallucination**: The Financial Agent (`FinancialAgent`) must NEVER fabricate numbers, loan balances, interest rates, or card limits. All financial figures must come strictly from the database via `TransactionTools`, `CashFlowTools`, `CreditCardTools`, `LoanTools`, and `SavingGoalTools`. If an entity does not exist in the DB, the agent must report that no records exist.
8. **Computed Financial Fields**: Computed metrics such as `progress_percentage` in `saving_goals` and `available_credit` in `credit_cards` must be attached consistently on both reads and write/update operations so client callers receive complete models.

### E. End-to-End Diagnostics & Connectivity Protocol
1. **Frontend-Backend Contract Parity**:
   - The root `src/` directory (consumed by Expo) and `mobile/src/` MUST be kept 100% synchronized at all times.
   - All response schemas defined in FastAPI (`ChatResponse`, `VoiceUploadResponse`, `db/status`) must have identical TypeScript interfaces in `src/services/api.ts` (`ChatResponse`, `VoiceResponse`, `DatabaseStatusResponse`).
2. **Detailed Error Surfacing**:
   - Client fetch methods (`sendChatMessage`, `checkDatabaseStatus`, `sendAudioRecording`) must parse `errorData.detail` from FastAPI error payloads so users and developers see the real reason for failures rather than generic HTTP status codes.
3. **Multi-Layer Diagnostic Tooling**:
   - The diagnostic screen (`ConnectionDiagnosticScreen.tsx`) must maintain dedicated, independent checks for:
     a) Backend process liveness (`GET /health`).
     b) Database / Supabase connectivity (`GET /db/status`).
     c) Agent orchestration & LLM synthesis (`POST /chat`).
   - This isolates whether an issue stems from local networking, backend process crashes, or database outages.

### F. Email Integration & Human-in-the-Loop Safeguards
1. **Mandatory Human Confirmation**:
   - The Assistant must NEVER automatically dispatch emails without explicit confirmation from the user (`confirmed=True`).
   - When a user requests sending an email, the backend prepares a draft and sets `requires_confirmation: True`, presenting recipient, subject, and content to the user.
   - Dispatch only executes when the user confirms with affirmative input ("sí", "confirmo", "envíalo", "adelante"). If the user cancels or says "no", the pending email draft is cleanly discarded.
2. **Extensible Email Client Architecture**:
   - `BaseEmailClient` provides an abstract interface for email operations (`list_unread`, `search_emails`, `send_email`, `create_draft`).
   - `ImapEmailClient` connects to IMAP (with SSL support) and SMTP for real-world mailboxes.
   - `MockEmailClient` provides deterministic offline/testing operation and seamless Supabase database synchronization.

### G. Text-To-Speech (TTS) & Audio Presentation
1. **Persistent Text Display**:
   - The textual response MUST ALWAYS remain visible in the conversation list regardless of whether speech audio is played.
2. **Markdown Stripping for Speech**:
   - Before passing assistant response text to the TTS engine (`expo-speech` or backend), markdown syntax (`**bold**`, `# header`, `*bullet*`, etc.) must be stripped via `stripMarkdownForTTS(text)` so the voice synthesizer pronounces natural words rather than punctuation characters.
3. **Audio Collision Prevention**:
   - Starting a new voice recording or sending a text message must immediately stop any active speech playback (`Speech.stop()`).
4. **Backend TTS Sizing & MIME Types**:
   - The `/tts` endpoint and static audio handler must always stream standard `audio/wav` with valid RIFF headers and non-zero byte size to ensure compatibility with mobile players.

### H. Android Notification Ingestion & Automation
1. **Expo Go vs Native Android**:
   - In Expo Go (standard client), arbitrary native Java/Kotlin services (`NotificationListenerService`) cannot be executed without `expo prebuild`.
   - For live workshop testing on physical devices, use **MacroDroid** (or Automate/Tasker) which natively binds `NotificationListenerService` and dispatches HTTP `POST` requests to `/webhooks/bank` via Tailscale/LAN.
   - For in-app simulation, `NotificationAutomationScreen.tsx` provides presets and real-time transaction monitoring with direct feedback from the LLM Structured Output.
### I. Tailscale Private Remote Networking (Fase 16)
1. **Host Network Binding**:
   - FastAPI (`backend/app/core/config.py`) maintains `HOST="0.0.0.0"`, automatically binding to loopback (`127.0.0.1`), LAN Wi-Fi (`192.168.x.x`), and Tailscale adapter (`100.x.y.z`).
2. **Zero Public Port Forwarding**:
   - Tailscale creates an end-to-end encrypted WireGuard overlay mesh network (CGNAT `100.64.0.0/10`). No ports need to be opened on residential or external routers.
3. **Mobile Dual-Network Ergonomics**:
   - `ConnectionDiagnosticScreen.tsx` provides 1-tap switching between `[🏠 LAN Wi-Fi]` and `[🔒 Tailscale (4G/Remoto)]`, maintaining 100% parity between `src/` and `mobile/src/`.
4. **CLI Process Hygiene on Windows**:
   - Never leave blocking `tailscale up` or `tailscale login` CLI processes lingering in background without timeouts; the native Windows GUI (`tailscale-ipn.exe`) handles interactive authentication seamlessly.

### J. Security Hardening & Secret Management (Fase 17)
1. **Strict Git Exclusion for Environment Secrets**:
   - `.env` and `.env.*` MUST ALWAYS be listed in `.gitignore` (with exception for `!.env.example`).
   - NEVER commit `.env` to Git. Verify with `git check-ignore -v .env` before committing any phase.
   - Maintain `.env.example` in the project root and `backend/.env.example` with up-to-date documentation and placeholders.
2. **Bearer Token & Webhook Authentication**:
   - Protected endpoints (`/chat`, `/voice`, `/tts`, `/db/status`, `/webhooks/bank/recent`) validate `Authorization: Bearer <token>` or `X-API-Key: <token>` using constant-time comparison (`secrets.compare_digest`).
   - Webhook endpoint (`/webhooks/bank`) validates `X-Webhook-Secret: <secret>` using `secrets.compare_digest`.
   - When `API_BEARER_TOKEN` or `BANK_WEBHOOK_SECRET` are empty (`""`) in `.env`, the backend runs in permissive development mode with security notices in console. When configured, unauthenticated requests are strictly rejected with HTTP 401.
   - Public endpoints (`/`, `/health`, `/docs`, `/openapi.json`) remain accessible without tokens.
3. **Defense-in-Depth Input Validation**:
   - `ChatRequest`: Enforce length constraints (1 to 4096 chars) and whitespace stripping.
   - `VoiceUpload`: Enforce 25MB maximum upload limit (HTTP 413) and sanitize filenames on disk using UUID prefixes to block Directory Traversal attacks while preserving client filename in response.
   - `TTS`: Enforce maximum 2000 chars text limit and sanitize audio file requests to prevent path traversal outside `TTS_DIR`.
   - `BankWebhookPayload`: Enforce 2000 chars max content limit, validate UUID syntax for optional `user_id`.
4. **API Key URL Sanitization**:
   - External LLM REST calls (Google AI Studio) MUST pass `x-goog-api-key` in HTTP headers instead of appending `?key=` query parameters to avoid leaking secrets in proxy or server logs.
5. **Mobile-Backend Auth Parity**:
   - Maintain 100% parity between `src/services/api.ts` and `mobile/src/services/api.ts`. Both attach `getAuthHeaders()` to all protected backend calls and inject `X-Webhook-Secret` into bank webhooks.

### K. Full End-to-End System Integration (Fase 18)
1. **Cross-Module Transaction State Parity**:
   - In both live Supabase PostgreSQL and offline in-memory fallback, transaction storage in `TransactionTools` (`_shared_transactions`) and `CashFlowTools` must remain 100% synchronized across `webhooks.py`, `FinancialAgent`, and `ToolDispatcher`.
   - When a bank notification is ingested via `POST /webhooks/bank`, any subsequent voice or chat query to the Financial Agent immediately includes the transaction and reflects it in liquid balance calculations.
2. **Orchestrator LLM State Hygiene**:
   - In unit/integration tests and dynamic runtime reconfiguration, always reset `orchestrator.set_llm_service(None)` in both `setUp()` and `tearDown()` to prevent mock LLM instances or canned structured intents from leaking across distinct test files or runtime contexts.
3. **Dual Pipeline Coexistence**:
   - The conversational pipeline (`Mobile -> Voice -> Backend -> STT -> Orchestrator -> Sub-Agents -> DB -> TTS -> Mobile`) and the passive notification pipeline (`Bank Push -> Webhook -> LLM Extraction -> DB -> Financial Agent`) operate concurrently without blocking, sharing state through the database layer.

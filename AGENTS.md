# Project Guidelines & Architecture: Multi-Agent Personal Assistant

## Expo Documentation Rule
Read the exact versioned docs at https://docs.expo.dev/versions/v57.0.0/ before writing any mobile code.

---

## 1. Core Workflow Directives
- **Phased & Progressive Development**: DO NOT attempt to build the entire project all at once. Build strictly phase-by-phase. Each phase MUST be fully functional and verified before proceeding to the next.
- **Spec-Driven**: Every phase and component must adhere to the Spec-Driven Development (SDD) contract before code is written.
- **Responsive UI & Keyboard Ergonomics**: All mobile screens and components MUST be fully responsive across various device sizes. The virtual keyboard MUST properly displace the screen so that input bars, send buttons, and conversation contents are never hidden or obscured when the keyboard is open.
- **Mandatory App Testing Instructions in Phase Reports**: In EVERY phase completion report / walkthrough, ALWAYS provide explicit, step-by-step instructions explaining exactly how the user can test and experience the newly implemented features directly from the mobile application (Expo Go) and/or backend endpoints.

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

### C. LLM & Connectivity (Learned Gotchas)
1. **Google AI Studio Credentials & Models**:
   - Both `AQ.Ab8...` tokens and `AIzaSy...` keys are valid depending on the Google endpoint.
   - The active model for this environment is `gemini-3.6-flash` (older models like `gemini-2.0-flash` are deprecated with 404).
   - Ensure the model name configured matches the provider's active catalog (`gemini-3.6-flash`).
2. **Mobile Client Fetch Timeouts**:
   - `sendChatMessage` and agent-handling endpoints in `mobile/src/services/api.ts` MUST have a timeout of at least `35000ms` (35s) to accommodate multi-step reasoning, tool execution, and LLM inference without aborting prematurely.
3. **Instant Graceful Degradation**:
   - If the selected LLM provider (Ollama, Gemini) is unresponsive or misconfigured, agents MUST degrade gracefully and return structured tool responses immediately rather than timing out and leaving the user without an answer.

### D. Database & Tool Contracts (Supabase / PostgreSQL)
1. **UUID Columns**: In PostgreSQL, tables (`tasks`, `emails`, `users`) define `id UUID PRIMARY KEY`. NEVER insert arbitrary string prefixes (like `t-12345` or `draft-12345`). ALWAYS use valid standard UUIDs (`str(uuid.uuid4())`).
2. **Column Naming**: Verify active SQL schemas before crafting queries (e.g. `financial_accounts.account_name`, not `name`).
3. **Seed & In-Memory Synchronization**: Tools must combine or fall back seamlessly between live Supabase records and in-memory mock repositories so unit tests and offline workflows remain 100% deterministic.




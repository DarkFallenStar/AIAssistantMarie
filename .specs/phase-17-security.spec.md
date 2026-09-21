# Specification: Phase 17 — Security Hardening & Secret Management

## 1. Scope & Objectives
Implement enterprise-grade security hardening across both the FastAPI backend and React Native (Expo) mobile client:
1. Environment variables and secret isolation outside of source control (Git).
2. Creation and maintenance of `.env` and `.env.example` templates.
3. Strict zero-exposure of secrets in Git (`.gitignore` enforcement and verification).
4. Robust input validation and defense-in-depth sanitization on all endpoints.
5. Bearer token / API key authentication on protected endpoints.
6. Bank webhook authentication and constant-time secret validation (`hmac.compare_digest`).
7. HTTPS / Tailscale transport security guidelines and support.
8. Elimination of hardcoded keys and API key URL query leakage.

### Problem Definition
As the system evolves with multi-agent orchestration, database synchronization (Supabase), financial webhooks, speech processing, and remote Tailscale connectivity, endpoints must be safeguarded against unauthorized access, replay or spoofed webhooks, malformed or malicious inputs, memory exhaustion DoS attacks, and credential leaks in source repositories or HTTP query logs.

### Non-Goals
- Multi-user OAuth2/OpenID Connect identity provider rollout (this phase focuses on personal assistant private single-user token & webhook authentication).
- Public internet certificate authority (ACME/Let's Encrypt) issuance, since remote access is secured via Tailscale WireGuard mesh encryption.

---

## 2. System Topology & Security Architecture

```
[ MOBILE CLIENT (Expo Go / Android) ]
       │
       │ Bearer Token: 'Authorization: Bearer <API_BEARER_TOKEN>'
       │ Webhook Secret: 'X-Webhook-Secret: <BANK_WEBHOOK_SECRET>'
       │
       ▼ (Tailscale WireGuard / HTTPS Encrypted Transport)
[ FASTAPI BACKEND (0.0.0.0:8000) ]
       │
       ├─► [Security Middleware / Dependencies]
       │     ├─ verify_api_bearer_token (Constant-time token validation)
       │     └─ verify_bank_webhook_secret (Constant-time webhook secret check)
       │
       ├─► [Input Validation Layer (Pydantic V2)]
       │     ├─ ChatRequest: length bounds [1, 4096], whitespace stripping
       │     ├─ TTSRequest: length bounds [1, 2000], whitespace stripping
       │     ├─ BankWebhookPayload: bounds, UUID validation
       │     └─ VoiceUpload: 25MB max size, MIME validation, filename sanitization
       │
       ├─► [Protected API Endpoints]
       │     ├─ /chat (Token Protected)
       │     ├─ /voice (Token Protected, multipart validated)
       │     ├─ /tts (Token Protected)
       │     ├─ /db/status (Token Protected)
       │     └─ /webhooks/bank (Secret Protected)
       │
       └─► [External APIs (Google AI Studio)]
             └─ Header 'x-goog-api-key' (Zero query-string secret leakage)
```

---

## 3. Contracts & Technical Requirements

### A. Environment & Secret Isolation
- **Files**:
  - Root `.env`: Contains live or local development secrets (IGNORED by Git).
  - Root `.env.example`: Comprehensive, documented template without real keys.
  - Backend `.env.example`: Synchronized backend-specific template.
- **Git Invariant**:
  - `.gitignore` MUST contain `.env`, `.env.*`, and `!.env.example`.
  - `git check-ignore -v .env` MUST return code 0.
  - No secrets, tokens, or live credentials shall exist in tracked Git files.

### B. Authentication Contract (`backend/app/core/security.py`)
- **Header**: `Authorization: Bearer <token>` or `X-API-Key: <token>`.
- **Behavior**:
  - If `settings.API_BEARER_TOKEN` is configured:
    - Valid token: HTTP 200 / execution proceeds.
    - Invalid or missing token: HTTP 401 Unauthorized (`{"detail": "Token de autorización inválido o ausente"}`).
  - If `settings.API_BEARER_TOKEN` is empty (development fallback):
    - Requests proceed without blocking, with a clear `[SECURITY]` warning in console.
- **Public Endpoints (Unauthenticated)**:
  - `GET /` (API info)
  - `GET /health` (Liveness probe)
  - `GET /docs`, `GET /redoc`, `GET /openapi.json` (Documentation)

### C. Webhook Validation Contract (`backend/app/api/endpoints/webhooks.py`)
- **Header**: `X-Webhook-Secret: <secret>`.
- **Behavior**:
  - If `settings.BANK_WEBHOOK_SECRET` is configured:
    - Matches secret via `secrets.compare_digest`: Proceed.
    - Missing or invalid: HTTP 401 Unauthorized (`{"detail": "Webhook secret inválido o ausente"}`).
  - If `settings.BANK_WEBHOOK_SECRET` is empty:
    - Development warning logged; proceed.

### D. Input Validation & Defense-in-Depth Contracts
- **ChatRequest (`backend/app/schemas/chat.py`)**:
  - `message`: `str`, min length 1, max length 4096. Must not be empty or whitespace-only.
- **TTSRequest (`backend/app/api/endpoints/tts.py`)**:
  - `text`: `str`, min length 1, max length 2000. Must not be empty or whitespace-only.
- **BankWebhookPayload (`backend/app/schemas/webhook.py`)**:
  - `source`: `str`, min length 1, max length 100.
  - `content`: `str`, min length 1, max length 2000.
  - `user_id`: Optional, but if provided, must pass UUID format validation.
- **VoiceUpload (`backend/app/api/endpoints/voice.py`)**:
  - Max file size: 25MB (26,214,400 bytes). If exceeded: HTTP 413.
  - Allowed MIME types: `audio/*`, `application/octet-stream`.
  - Path traversal defense: sanitized basename, UUID prefixing.
- **TTS Path Traversal Defense (`backend/app/api/endpoints/tts.py`)**:
  - Path resolution strictly contained within `TTS_DIR`.

### E. LLM API Key Security (`backend/app/services/llm/google.py`)
- Request to Google Generative Language API MUST pass `x-goog-api-key` in HTTP headers.
- Query string `?key=...` MUST NOT be used, preventing secret exposure in URL logs.

### F. Mobile Client Contract (`src/` and `mobile/src/`)
- Maintain 100% parity between `src/` and `mobile/src/`.
- `config/index.ts`:
  - Export `API_TOKEN` and `BANK_WEBHOOK_SECRET` loaded from `process.env.EXPO_PUBLIC_*`.
- `services/api.ts`:
  - Automatically append `Authorization: Bearer <token>` when `API_TOKEN` is present.
  - Automatically append `X-Webhook-Secret: <secret>` on `sendBankWebhook`.

---

## 4. Acceptance Criteria & Scenarios (Gherkin)

```gherkin
Feature: Phase 17 — Security Hardening & Secret Management

  Scenario: Git ignores sensitive environment files
    Given a local .env file with secrets
    When git check-ignore is executed on .env
    Then the exit code must be 0 and matched by .gitignore

  Scenario: Chat request with whitespace-only input is rejected
    Given a chat request with message "   "
    When POST /chat is called
    Then the response status must be 422 or 400 with a descriptive validation error

  Scenario: Chat request exceeding maximum length is rejected
    Given a chat request with a message of 5000 characters
    When POST /chat is called
    Then the response status must be 422 with a length validation error

  Scenario: Voice upload exceeding file size limit is rejected
    Given an audio file upload larger than 25MB
    When POST /voice is called
    Then the response status must be 413 Payload Too Large

  Scenario: Protected endpoint rejects request with invalid bearer token
    Given API_BEARER_TOKEN is configured in backend settings
    When POST /chat is called with header "Authorization: Bearer wrong-token"
    Then the response status must be 401 Unauthorized

  Scenario: Protected endpoint accepts request with valid bearer token
    Given API_BEARER_TOKEN is configured in backend settings
    When POST /chat is called with header "Authorization: Bearer valid-token"
    Then the response status must be 200 OK

  Scenario: Bank webhook rejects request with invalid secret
    Given BANK_WEBHOOK_SECRET is configured in backend settings
    When POST /webhooks/bank is called with header "X-Webhook-Secret: invalid"
    Then the response status must be 401 Unauthorized

  Scenario: Bank webhook accepts request with valid secret
    Given BANK_WEBHOOK_SECRET is configured in backend settings
    When POST /webhooks/bank is called with header "X-Webhook-Secret: valid-secret"
    Then the response status must be 200 OK
```

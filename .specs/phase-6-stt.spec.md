# Specification Contract: Fase 6 — Speech To Text (STT)

## 1. Scope & Objectives
- **Problem Statement**: The application currently records audio in the mobile app and receives binary audio in `POST /voice`, but does not convert audio into text.
- **Objective**: Implement Speech To Text (STT) conversion:
  `AUDIO -> SPEECH TO TEXT -> TEXT`
  The transcribed text serves directly as the input to the Orchestrator.
- **Example Flow**:
  - Spoken Audio: *"¿Cuánto dinero me queda disponible para salir este fin de semana?"*
  - STT Transcription: *"¿Cuánto dinero me queda disponible para salir este fin de semana?"*
  - Orchestrator Input: Transcribed text routed to the multi-agent system.
  - Mobile UI: Displays the transcribed text as the user's speech bubble and presents the orchestrator's response.

---

## 2. Architecture & Contracts

### 2.1 Backend Pipeline
```
[POST /voice (binary audio)]
            │
            ▼
[Audio Validation & Storage] -> uploads/audio/<filename>
            │
            ▼
[STT Service (Whisper / faster-whisper)]
            │ (transcribed_text: str)
            ▼
[Orchestrator Service (app.agents.orchestrator)]
            │ (OrchestratorResponse)
            ▼
[VoiceUploadResponse JSON] -> Mobile Client
```

### 2.2 API Contract: `POST /voice` & `POST /api/voice`
- **Request**:
  - `multipart/form-data`
  - Field name: `file`
  - Type: Binary audio (M4A / AAC / WAV)
- **Response Model (`VoiceUploadResponse`)**:
  ```python
  class VoiceUploadResponse(BaseModel):
      status: str                   # "success" | "received"
      filename: str                 # "recording.m4a"
      size_bytes: int               # byte count
      content_type: Optional[str]   # MIME type
      transcribed_text: str         # Transcribed utterance
      intent: Optional[str]         # Intent category (financial, secretary, general)
      message: str                  # Diagnostic/status summary
      response: str                 # Assistant/orchestrator response text
  ```

### 2.3 STT Engine Abstraction (`app/audio/stt.py`)
- `BaseSTTService(ABC)`:
  - Method: `transcribe(audio_path: Path | str, language: str = "es") -> str`
- `WhisperSTTService(BaseSTTService)`:
  - Engine: `faster-whisper`
  - Parameters: `model_size` ("base" default), `device="cpu"`, `compute_type="int8"`
  - Logging: Windows-safe ASCII logs (`[STT] ...`)
- `MockSTTService(BaseSTTService)`:
  - Deterministic transcription for tests and environments without model download.

### 2.4 Orchestrator Interface (`app/agents/orchestrator.py`)
- `OrchestratorService`:
  - Method: `async def process_user_input(text: str) -> OrchestratorResponse`
  - Routes text to intent (financial vs secretary vs general query).
  - Returns structured `OrchestratorResponse(text=..., intent=..., response=...)`.

---

## 3. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Successful Audio Transcription & Orchestrator Routing
- **Given** an audio recording containing Spanish speech *"¿Cuánto dinero me queda disponible para salir este fin de semana?"*
- **When** the client sends a `POST` request to `/voice` with the audio file
- **Then** the backend returns HTTP 200
- **And** the response payload contains `transcribed_text` matching the spoken words
- **And** the response contains the orchestrator's generated reply
- **And** the mobile app renders the transcribed text in the user's message bubble.

### Scenario 2: Empty or Corrupted Audio
- **Given** an audio file with 0 bytes or an invalid audio format
- **When** the client sends a `POST` request to `/voice`
- **Then** the backend returns HTTP 400 with a descriptive error detail
- **And** the mobile app displays an inline error alert without crashing.

### Scenario 3: Audio with Silence or No Recognizable Speech
- **Given** an audio recording containing only background silence
- **When** the STT service processes the audio
- **Then** the service returns an empty string or handles silence gracefully
- **And** the orchestrator informs the user: *"No logré escuchar con claridad tu consulta, ¿podrías repetirla?"*

---

## 4. Impacted Components
- `backend/requirements.txt`: Add `faster-whisper>=1.0.0`
- `backend/app/core/config.py`: Add Whisper configuration settings (`WHISPER_MODEL_SIZE`, etc.)
- `backend/app/audio/stt.py`: STT engine abstraction & Whisper implementation
- `backend/app/agents/orchestrator.py`: Orchestrator service consuming transcribed text
- `backend/app/schemas/voice.py`: Schema update with `transcribed_text` and `intent`
- `backend/app/api/endpoints/voice.py`: Integration of STT and Orchestrator
- `backend/tests/test_stt.py`: Automated unit & integration tests for STT and Orchestrator
- `mobile/src/services/api.ts` & `src/services/api.ts`: Update `VoiceResponse` type definition
- `mobile/src/screens/AssistantScreen.tsx` & `src/screens/AssistantScreen.tsx`: Update voice bubble with recognized text

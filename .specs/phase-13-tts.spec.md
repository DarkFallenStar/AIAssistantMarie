# Specification: Phase 13 — Text-To-Speech (TTS) Integration

## 1. Scope & Objectives
Implement Text-To-Speech (TTS) synthesis and playback following the user flow:
```
Respuesta del backend
        ↓
Texto
        ↓
TTS
        ↓
Audio
        ↓
Usuario escucha respuesta
```
**Key Requirement**: The textual response MUST remain visible on the screen (`La respuesta también debe permanecer visible en pantalla`) at all times.

### Goals
1. **Backend TTS Engine & Endpoints**:
   - Create `BaseTTSService`, `MockTTSService` (deterministic offline `.wav` generator), and live/extensible TTS service in `backend/app/audio/tts.py`.
   - Implement `POST /tts` endpoint accepting text and generating audio.
   - Update `ChatResponse` and `VoiceUploadResponse` schemas with optional `audio_url: Optional[str]`.
   - Expose generated TTS audio files statically or via stream.
2. **Mobile Client Synthesis & Playback (Expo SDK 57)**:
   - Integrate `expo-speech` for native, instant, offline-capable device speech synthesis.
   - Automatically speak assistant responses upon receipt (both from text chats and voice uploads).
   - Display message text immediately and keep it persistently visible on the screen.
   - Add a speaker button (`🔊`) to each assistant message bubble to replay TTS on demand.
   - Implement audio conflict prevention: stop ongoing speech immediately if the user taps the microphone or submits a new text query.
   - Add a Mute/Audio toggle in the UI so the user can easily toggle voice narration.
3. **Frontend-Backend Contract Parity**:
   - Update `src/services/api.ts` and `mobile/src/services/api.ts` with `audio_url` in `ChatResponse` and `VoiceResponse`.
   - Provide helper `requestTTS(baseUrl, text)` in `api.ts`.
4. **Resilience & Testing**:
   - Deterministic unit tests in `backend/tests/test_tts.py` testing TTS generation, endpoint response, and audio headers.

---

## 2. API & Data Contracts

### Backend Endpoints
- `POST /tts`:
  - Request: `{"text": "Hola, ¿cómo estás?", "voice": "es"}`
  - Response: Audio file / stream (`audio/wav` or `audio/mpeg`) or JSON `{"status": "success", "audio_url": "/static/audio/tts/<id>.wav", "text": "..."}`.
- `GET /audio/tts/{filename}` (or static mount):
  - Returns raw audio stream with appropriate MIME type.

### Schema Updates
- `ChatResponse`:
  ```python
  class ChatResponse(BaseModel):
      response: str
      intent: Optional[str] = None
      agent: Optional[str] = None
      tools_executed: Optional[List[str]] = Field(default_factory=list)
      structured_intent: Optional[Dict[str, Any]] = None
      audio_url: Optional[str] = None
  ```
- `VoiceUploadResponse`:
  ```python
  class VoiceUploadResponse(BaseModel):
      status: str
      filename: str
      size_bytes: int
      content_type: Optional[str] = None
      transcribed_text: Optional[str] = None
      intent: Optional[str] = None
      message: str
      response: str
      audio_url: Optional[str] = None
  ```

---

## 3. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Text Chat Response with TTS Playback
- **Given** the mobile app is connected to the backend.
- **When** the user sends a text message (e.g. "Hola").
- **Then** the backend responds with text.
- **And** the text is immediately displayed in a message bubble in the conversation list.
- **And** the assistant automatically speaks the response aloud using TTS in Spanish.

### Scenario 2: Voice Query with TTS Playback
- **Given** the user records an audio query and uploads it to `POST /voice`.
- **When** the backend transcribes the audio and generates the orchestrator response.
- **Then** the transcribed text and assistant response are rendered in the message list.
- **And** the assistant automatically speaks the response aloud.

### Scenario 3: On-Demand Replay
- **Given** an assistant message is displayed on screen.
- **When** the user taps the speaker button (`🔊`) on that message bubble.
- **Then** the message's text is spoken aloud again.

### Scenario 4: Interruption Protection
- **Given** the assistant is currently speaking via TTS.
- **When** the user starts recording voice or sends a new text message.
- **Then** the TTS playback stops immediately without audio overlapping.

### Scenario 5: Markdown Stripping for Natural Pronunciation
- **Given** a response containing markdown formatting (e.g. `**importante**`, `# Resumen`).
- **When** the text is passed to TTS.
- **Then** the markdown formatting symbols are stripped so the synthesizer speaks smoothly without reading symbols.

---

## 4. Impacted Components
- `backend/app/audio/tts.py` [NEW]
- `backend/app/api/endpoints/tts.py` [NEW]
- `backend/app/main.py` [MODIFY]
- `backend/app/schemas/chat.py` [MODIFY]
- `backend/app/schemas/voice.py` [MODIFY]
- `backend/tests/test_tts.py` [NEW]
- `src/services/api.ts` & `mobile/src/services/api.ts` [MODIFY]
- `src/components/MessageBubble.tsx` & `mobile/src/components/MessageBubble.tsx` [MODIFY]
- `src/components/MessageList.tsx` & `mobile/src/components/MessageList.tsx` [MODIFY]
- `src/screens/AssistantScreen.tsx` & `mobile/src/screens/AssistantScreen.tsx` [MODIFY]

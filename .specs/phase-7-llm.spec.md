# Specification Contract: Fase 7 — LLM (Language Model Service Layer)

## 1. Scope & Objectives
- **Problem Statement**: The application currently has placeholder responses in the Chat endpoint and hardcoded template responses in the Orchestrator service. Agents are not connected to a real LLM, and there is no provider-agnostic abstraction layer to switch seamlessly between local models (Ollama) and cloud models (Google AI Studio / Gemini).
- **Objective**: Implement a decoupled, provider-agnostic **LLM SERVICE** layer:
  ```
  LLMService (Base Interface)
      ├── OllamaService (Local via Ollama REST API)
      ├── GoogleAIService (Cloud via Gemini REST API)
      └── MockLLMService (Deterministic testing / Offline)
  ```
- **Guarantees**:
  - The rest of the application and future specialized agents (Secretary, Financial, etc.) interact *only* with the abstract `BaseLLMService` contract.
  - The provider can be configured via environment variables (`LLM_PROVIDER="ollama"` | `"google"` | `"mock"`) or swapped at runtime without altering agent or endpoint logic.
  - Zero raw UTF-8 / emoji prints to Windows stdout (strict zero-regression compliance with ASCII logging tags like `[LLM]`, `[OLLAMA]`, `[GEMINI]`).

---

## 2. Architecture & Contracts

### 2.1 Component Topology
```
[Agent / Orchestrator / Chat Endpoint]
                 │
                 ▼
     [get_llm_service() Factory]
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
[OllamaService] [GoogleAIService] [MockLLMService]
   │             │             │
   ▼             ▼             ▼
(Local HTTP)  (Cloud HTTPS)  (In-Memory)
```

### 2.2 Domain Data Contracts (`app/schemas/llm.py` or `app/services/llm/base.py`)
```python
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class LLMMessage(BaseModel):
    role: LLMRole = Field(..., description="Role of the speaker (system, user, assistant)")
    content: str = Field(..., description="Message text content")

class LLMResponse(BaseModel):
    text: str = Field(..., description="Generated text response")
    provider: str = Field(..., description="Provider name (ollama, google, mock)")
    model: str = Field(..., description="Model identifier used")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw provider payload for debugging")
```

### 2.3 Abstract Interface (`app/services/llm/base.py`)
```python
from abc import ABC, abstractmethod

class BaseLLMService(ABC):
    """
    Abstract contract for Language Model Services.
    All providers must implement these asynchronous methods.
    """
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Single-turn generation from a prompt string."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Multi-turn conversation generation from a list of structured messages."""
        pass
```

### 2.4 Concrete Implementations
1. **`OllamaService`** (`app/services/llm/ollama.py`):
   - Base URL: `settings.OLLAMA_BASE_URL` (default: `http://localhost:11434`).
   - Default Model: `settings.OLLAMA_MODEL` (default: `llama3.2`).
   - Transport: Asynchronous HTTP via `httpx.AsyncClient`.
   - Endpoint: `/api/chat` with structured messages.
   - Error Handling: Catches connection timeouts and network errors gracefully, raising domain-specific `LLMConnectionError`.

2. **`GoogleAIService`** (`app/services/llm/google.py`):
   - Base URL: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}`.
   - Default Model: `settings.GEMINI_MODEL` (default: `gemini-2.0-flash`).
   - Transport: Asynchronous HTTP via `httpx.AsyncClient`.
   - Payload Mapping:
     - Converts `LLMMessage(role=USER)` to `contents: [{role: "user", parts: [{text: "..."}]}]`.
     - Converts `LLMMessage(role=ASSISTANT)` to `contents: [{role: "model", parts: [{text: "..."}]}]`.
     - Maps `system_prompt` to `systemInstruction`.
   - Error Handling: Validates presence of `GEMINI_API_KEY` and handles HTTP/Quota errors gracefully.

3. **`MockLLMService`** (`app/services/llm/mock.py`):
   - In-memory deterministic responses for automated test suites and offline environments.
   - Configurable canned response or dynamic prefixing.

4. **Factory & Provider Resolver** (`app/services/llm/__init__.py`):
   - `get_llm_service(provider: Optional[str] = None) -> BaseLLMService`: Returns configured singleton or requested instance.
   - `set_llm_service(service: Optional[BaseLLMService]) -> None`: Test injection override.

---

## 3. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Unified Interface Transparency
- **Given** an application agent initialized with `get_llm_service()`
- **When** the agent invokes `llm.generate("¿Cuál es el saldo de mi cuenta?")`
- **Then** the agent receives an `LLMResponse` containing a non-empty `text` string and provider metadata
- **And** the agent code does not contain any provider-specific imports or JSON schemas.

### Scenario 2: Dynamic Provider Switching
- **Given** the system is configured with `LLM_PROVIDER="mock"`
- **When** the provider setting is updated to `"google"` or `"ollama"`
- **Then** `get_llm_service()` returns the corresponding concrete implementation (`GoogleAIService` or `OllamaService`) without requiring refactoring in calling agents.

### Scenario 3: Ollama Chat Payload Formatting
- **Given** an active `OllamaService` instance
- **When** calling `chat(messages=[LLMMessage(role="user", content="Hola")])`
- **Then** the service sends a well-formed JSON request to `/api/chat` with `{ "model": "...", "messages": [...], "stream": false }`
- **And** extracts `message.content` from the response.

### Scenario 4: Google AI Studio Content Mapping
- **Given** an active `GoogleAIService` instance with a valid API key
- **When** calling `chat()` or `generate()` with a system prompt and user message
- **Then** the service translates messages to Gemini's `contents` and `systemInstruction` format
- **And** extracts `candidates[0].content.parts[0].text`.

### Scenario 5: Graceful Error Handling & Fallback
- **Given** a provider that is unreachable or returns an HTTP 500/timeout
- **When** an agent calls `generate()` or `chat()`
- **Then** the service catches the network fault and raises `LLMServiceError` with descriptive diagnostics rather than crashing unhandled
- **And** the calling agent/orchestrator can offer a graceful fallback message.

---

## 4. Impacted Components
- `backend/app/core/config.py`: Verify and ensure `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL` are present.
- `backend/app/schemas/llm.py`: Pydantic models for `LLMRole`, `LLMMessage`, `LLMResponse`.
- `backend/app/services/llm/base.py`: Abstract base class `BaseLLMService` and domain exceptions (`LLMServiceError`, `LLMConnectionError`).
- `backend/app/services/llm/ollama.py`: `OllamaService` implementation.
- `backend/app/services/llm/google.py`: `GoogleAIService` implementation.
- `backend/app/services/llm/mock.py`: `MockLLMService` implementation.
- `backend/app/services/llm/__init__.py`: Factory methods `get_llm_service()`, `set_llm_service()`.
- `backend/app/agents/orchestrator.py`: Connect orchestrator to `BaseLLMService` for dynamic responses while preserving intent routing.
- `backend/app/api/endpoints/chat.py`: Connect `/chat` endpoint to `get_llm_service()`.
- `backend/tests/test_llm.py`: Comprehensive test suite verifying all concrete implementations, factory switching, payload serialization, and mock behavior.

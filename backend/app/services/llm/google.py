from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.llm import LLMRole, LLMMessage, LLMResponse
from app.services.llm.base import BaseLLMService, LLMConnectionError, LLMConfigurationError, LLMServiceError

class GoogleAIService(BaseLLMService):
    """
    LLM service implementation for Google AI Studio (Gemini) models via REST API.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self._model = (model or settings.GEMINI_MODEL or "gemini-3.8-flash").strip()
        self._timeout = timeout_seconds if timeout_seconds is not None else getattr(settings, "GEMINI_TIMEOUT_SECONDS", 25.0)

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        if not self._api_key or not self._api_key.strip():
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not set. Please configure GEMINI_API_KEY in .env to use Google AI Studio."
            )

        # Collect system prompts
        system_texts: List[str] = []
        if system_prompt:
            system_texts.append(system_prompt)

        gemini_contents: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_texts.append(msg.content)
            elif msg.role == LLMRole.ASSISTANT:
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })
            else:  # USER
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })

        payload: Dict[str, Any] = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature
            }
        }

        if max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        if system_texts:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_texts)}]
            }

        endpoint_url = f"{self.BASE_URL}/{self._model}:generateContent"
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json"
        }
        print(f"[GEMINI] Calling Google AI Studio for model '{self._model}' ({len(gemini_contents)} turns)...")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(endpoint_url, json=payload, headers=headers)

            if response.status_code != 200:
                print(f"[GEMINI] HTTP {response.status_code} error: {response.text}")
                raise LLMServiceError(f"Google AI Studio returned HTTP {response.status_code}: {response.text}")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMServiceError(f"Google AI Studio returned no candidates: {data}")

            candidate = candidates[0]
            parts = candidate.get("content", {}).get("parts", [])
            response_text = "".join(part.get("text", "") for part in parts).strip()

            print(f"[GEMINI] Response received ({len(response_text)} chars).")
            return LLMResponse(
                text=response_text,
                provider=self.provider_name,
                model=self._model,
                raw_response=data
            )

        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            err_msg = f"Cannot connect to Google AI Studio endpoint. Error: {exc}"
            print(f"[GEMINI] Connection error: {err_msg}")
            raise LLMConnectionError(err_msg) from exc
        except httpx.TimeoutException as exc:
            err_msg = f"Google AI Studio request timed out after {self._timeout}s"
            print(f"[GEMINI] Timeout error: {err_msg}")
            raise LLMConnectionError(err_msg) from exc
        except (LLMServiceError, LLMConfigurationError):
            raise
        except Exception as exc:
            err_msg = f"Unexpected error during Google AI Studio invocation: {exc}"
            print(f"[GEMINI] Error: {err_msg}")
            raise LLMServiceError(err_msg) from exc

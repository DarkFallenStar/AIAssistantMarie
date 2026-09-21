from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.llm import LLMRole, LLMMessage, LLMResponse
from app.services.llm.base import BaseLLMService, LLMConnectionError, LLMServiceError

class OllamaService(BaseLLMService):
    """
    LLM service implementation for local models served via Ollama REST API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

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
        messages: List[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))
        messages.append(LLMMessage(role=LLMRole.USER, content=prompt))
        return await self.chat(
            messages=messages,
            system_prompt=None,
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
        formatted_messages: List[Dict[str, str]] = []

        # If system_prompt is provided separately and not already the first message, prepend it
        if system_prompt and not (messages and messages[0].role == LLMRole.SYSTEM):
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })

        for msg in messages:
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        url = f"{self._base_url}/api/chat"
        print(f"[OLLAMA] Calling {url} with model '{self._model}' ({len(formatted_messages)} messages)...")

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=5.0)) as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                print(f"[OLLAMA] HTTP {response.status_code} error: {response.text}")
                raise LLMServiceError(f"Ollama returned HTTP {response.status_code}: {response.text}")

            data = response.json()
            message_obj = data.get("message", {})
            response_text = message_obj.get("content", "").strip()

            print(f"[OLLAMA] Response received ({len(response_text)} chars).")
            return LLMResponse(
                text=response_text,
                provider=self.provider_name,
                model=self._model,
                raw_response=data
            )

        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            err_msg = f"Cannot connect to Ollama at {self._base_url}. Is the Ollama daemon running? Error: {exc}"
            print(f"[OLLAMA] Connection error: {err_msg}")
            raise LLMConnectionError(err_msg) from exc
        except httpx.TimeoutException as exc:
            err_msg = f"Ollama request to {url} timed out after {self._timeout}s"
            print(f"[OLLAMA] Timeout error: {err_msg}")
            raise LLMConnectionError(err_msg) from exc
        except LLMServiceError:
            raise
        except Exception as exc:
            err_msg = f"Unexpected error during Ollama invocation: {exc}"
            print(f"[OLLAMA] Error: {err_msg}")
            raise LLMServiceError(err_msg) from exc

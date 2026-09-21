from typing import Optional, List, Dict, Any
from app.schemas.llm import LLMMessage, LLMResponse
from app.services.llm.base import BaseLLMService, LLMServiceError

class FailoverLLMService(BaseLLMService):
    """
    Dual-provider LLM service with automatic bidirectional failover.
    Coordinates between a primary and secondary provider (e.g., Google Gemini and Ollama).
    If the primary provider fails (timeout, connection error, rate limit, HTTP 5xx),
    it immediately and seamlessly delegates to the secondary provider, and vice-versa.
    """

    def __init__(
        self,
        primary_service: BaseLLMService,
        secondary_service: BaseLLMService,
    ):
        self._primary = primary_service
        self._secondary = secondary_service

    @property
    def primary(self) -> BaseLLMService:
        return self._primary

    @property
    def secondary(self) -> BaseLLMService:
        return self._secondary

    @property
    def provider_name(self) -> str:
        return f"{self._primary.provider_name}+{self._secondary.provider_name}"

    @property
    def model_name(self) -> str:
        return f"{self._primary.model_name} (failover: {self._secondary.model_name})"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            return await self._primary.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as primary_exc:
            print(
                f"[LLM-FAILOVER] Primary provider '{self._primary.provider_name}' failed: {primary_exc}. "
                f"Failing over to secondary provider '{self._secondary.provider_name}'..."
            )
            try:
                resp = await self._secondary.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(f"[LLM-FAILOVER] Failover to '{self._secondary.provider_name}' succeeded.")
                return resp
            except Exception as secondary_exc:
                print(
                    f"[LLM-FAILOVER] Secondary provider '{self._secondary.provider_name}' also failed: {secondary_exc}. "
                    f"All LLM providers exhausted."
                )
                raise LLMServiceError(
                    f"Dual LLM execution failed. Primary ({self._primary.provider_name}): {primary_exc}. "
                    f"Secondary ({self._secondary.provider_name}): {secondary_exc}"
                ) from secondary_exc

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            return await self._primary.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as primary_exc:
            print(
                f"[LLM-FAILOVER] Primary provider '{self._primary.provider_name}' failed: {primary_exc}. "
                f"Failing over to secondary provider '{self._secondary.provider_name}'..."
            )
            try:
                resp = await self._secondary.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(f"[LLM-FAILOVER] Failover to '{self._secondary.provider_name}' succeeded.")
                return resp
            except Exception as secondary_exc:
                print(
                    f"[LLM-FAILOVER] Secondary provider '{self._secondary.provider_name}' also failed: {secondary_exc}. "
                    f"All LLM providers exhausted."
                )
                raise LLMServiceError(
                    f"Dual LLM chat failed. Primary ({self._primary.provider_name}): {primary_exc}. "
                    f"Secondary ({self._secondary.provider_name}): {secondary_exc}"
                ) from secondary_exc

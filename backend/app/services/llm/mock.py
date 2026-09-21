from typing import Optional, List, Dict, Any
from app.schemas.llm import LLMRole, LLMMessage, LLMResponse
from app.services.llm.base import BaseLLMService

class MockLLMService(BaseLLMService):
    """
    Deterministic in-memory LLM service for testing and development.
    Requires no network connections or external daemons.
    """

    def __init__(
        self,
        canned_response: Optional[str] = None,
        model_name: str = "mock-model",
    ):
        self._canned_response = canned_response
        self._model_name = model_name
        self.history: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    def set_canned_response(self, response: str) -> None:
        self._canned_response = response

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
        self.history.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })

        if self._canned_response is not None:
            text = self._canned_response
        else:
            last_message = messages[-1].content if messages else ""
            text = f"Mock LLM Response for: {last_message}"

        print(f"[LLM-MOCK] Generated response ({len(text)} chars)")
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self._model_name,
            raw_response={"status": "mock", "generated_text": text}
        )

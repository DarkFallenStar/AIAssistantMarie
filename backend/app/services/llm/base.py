from abc import ABC, abstractmethod
from typing import Optional, List
from app.schemas.llm import LLMMessage, LLMResponse

class LLMServiceError(Exception):
    """Base exception for all LLM service failures."""
    pass

class LLMConnectionError(LLMServiceError):
    """Raised when an LLM provider endpoint is unreachable or times out."""
    pass

class LLMConfigurationError(LLMServiceError):
    """Raised when an LLM provider is misconfigured (e.g. missing API keys)."""
    pass

class BaseLLMService(ABC):
    """
    Abstract contract for Language Model Services.
    Decouples the rest of the application from specific providers (Ollama, Google AI, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation (e.g., 'ollama', 'google', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier being used by the provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a completion for a single prompt string.
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a completion for a structured multi-turn conversation.
        """
        pass

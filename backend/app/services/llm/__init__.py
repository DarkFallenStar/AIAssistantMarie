from typing import Optional
from app.core.config import settings
from app.services.llm.base import (
    BaseLLMService,
    LLMServiceError,
    LLMConnectionError,
    LLMConfigurationError,
)
from app.services.llm.ollama import OllamaService
from app.services.llm.google import GoogleAIService
from app.services.llm.mock import MockLLMService

__all__ = [
    "BaseLLMService",
    "OllamaService",
    "GoogleAIService",
    "MockLLMService",
    "LLMServiceError",
    "LLMConnectionError",
    "LLMConfigurationError",
    "get_llm_service",
    "set_llm_service",
]

_llm_service_instance: Optional[BaseLLMService] = None

def get_llm_service(provider: Optional[str] = None) -> BaseLLMService:
    """
    Factory function returning the active BaseLLMService instance.
    If an override is set via set_llm_service(), that instance is returned.
    Otherwise, instantiates the provider specified by the argument or settings.LLM_PROVIDER.
    """
    global _llm_service_instance
    if _llm_service_instance is not None:
        return _llm_service_instance

    target_provider = (provider or settings.LLM_PROVIDER).lower()

    if target_provider == "ollama":
        return OllamaService()
    elif target_provider in ("google", "gemini"):
        return GoogleAIService()
    elif target_provider == "mock":
        return MockLLMService()
    else:
        print(f"[LLM] Unknown provider '{target_provider}', falling back to MockLLMService")
        return MockLLMService()

def set_llm_service(service: Optional[BaseLLMService]) -> None:
    """
    Explicitly set or reset the LLM service instance (primarily used for test mocks).
    """
    global _llm_service_instance
    _llm_service_instance = service

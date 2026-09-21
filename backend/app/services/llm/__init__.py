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
from app.services.llm.failover import FailoverLLMService

__all__ = [
    "BaseLLMService",
    "OllamaService",
    "GoogleAIService",
    "MockLLMService",
    "FailoverLLMService",
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
    - If set_llm_service() was called with an override, that instance is returned.
    - If an explicit single provider is requested via argument ('ollama', 'google', 'mock'),
      it returns that single provider (enabling isolated testing).
    - If provider is 'dual' / 'hybrid' or omitted, returns a FailoverLLMService orchestrating
      both Google Gemini and local Ollama simultaneously with bidirectional failover.
    """
    global _llm_service_instance
    if _llm_service_instance is not None:
        return _llm_service_instance

    # Explicit single provider request (for isolated unit tests)
    if provider is not None:
        p_lower = provider.lower()
        if p_lower == "ollama":
            return OllamaService()
        elif p_lower in ("google", "gemini"):
            return GoogleAIService()
        elif p_lower == "mock":
            return MockLLMService()
        elif p_lower in ("dual", "hybrid", "failover"):
            return FailoverLLMService(
                primary_service=GoogleAIService(),
                secondary_service=OllamaService()
            )
        else:
            print(f"[LLM] Unknown provider '{p_lower}', falling back to MockLLMService")
            return MockLLMService()

    # Default configured provider from environment
    config_provider = settings.LLM_PROVIDER.lower()

    if config_provider in ("dual", "hybrid", "failover"):
        return FailoverLLMService(
            primary_service=GoogleAIService(),
            secondary_service=OllamaService()
        )
    elif config_provider in ("google", "gemini"):
        # Primary is Google, secondary is Ollama
        return FailoverLLMService(
            primary_service=GoogleAIService(),
            secondary_service=OllamaService()
        )
    elif config_provider == "ollama":
        # Primary is Ollama, secondary is Google
        return FailoverLLMService(
            primary_service=OllamaService(),
            secondary_service=GoogleAIService()
        )
    elif config_provider == "mock":
        return MockLLMService()
    else:
        print(f"[LLM] Unknown provider '{config_provider}', falling back to MockLLMService")
        return MockLLMService()

def set_llm_service(service: Optional[BaseLLMService]) -> None:
    """
    Explicitly set or reset the LLM service instance (used for test mocks).
    """
    global _llm_service_instance
    _llm_service_instance = service

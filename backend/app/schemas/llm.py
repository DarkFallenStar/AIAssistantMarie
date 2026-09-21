from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    GOOGLE = "google"
    MOCK = "mock"

class LLMMessage(BaseModel):
    role: LLMRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Text content of the message")

class LLMResponse(BaseModel):
    text: str = Field(..., description="Generated text response from the language model")
    provider: str = Field(..., description="Provider name (ollama, google, mock)")
    model: str = Field(..., description="Model identifier used")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw provider response payload")

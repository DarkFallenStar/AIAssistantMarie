from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        example="Hola",
        description="Mensaje enviado por el usuario"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("El mensaje no puede estar vacío ni contener solo espacios en blanco.")
        return cleaned

class ChatResponse(BaseModel):
    response: str = Field(..., example="Hola, soy tu asistente.", description="Respuesta del asistente")
    intent: Optional[str] = Field(default=None, description="Intención detectada por el orquestador")
    agent: Optional[str] = Field(default=None, description="Nombre del agente que generó la respuesta")
    tools_executed: Optional[List[str]] = Field(default_factory=list, description="Lista de herramientas ejecutadas")
    structured_intent: Optional[Dict[str, Any]] = Field(default=None, description="Intención estructurada extraída (Function Calling)")
    audio_url: Optional[str] = Field(default=None, description="URL del audio sintetizado TTS")

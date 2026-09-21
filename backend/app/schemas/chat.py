from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., example="Hola", description="Mensaje enviado por el usuario")

class ChatResponse(BaseModel):
    response: str = Field(..., example="Hola, soy tu asistente.", description="Respuesta del asistente")
    intent: Optional[str] = Field(default=None, description="Intención detectada por el orquestador")
    agent: Optional[str] = Field(default=None, description="Nombre del agente que generó la respuesta")

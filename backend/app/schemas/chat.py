from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., example="Hola", description="Mensaje enviado por el usuario")

class ChatResponse(BaseModel):
    response: str = Field(..., example="Hola, soy tu asistente.", description="Respuesta del asistente")

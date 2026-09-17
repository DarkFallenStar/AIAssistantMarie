from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Chat Básico (Fase 2)")
async def chat(payload: ChatRequest):
    """
    Endpoint inicial de chat para validar la comunicación móvil ↔ backend.
    En esta fase responde de forma estática antes de integrar los agentes LLM.
    """
    return ChatResponse(response="Hola, soy tu asistente.")

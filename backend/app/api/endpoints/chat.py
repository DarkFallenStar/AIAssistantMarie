from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.orchestrator import get_orchestrator_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Chat con Asistente / Orquestador Multi-Agente")
async def chat(payload: ChatRequest):
    """
    Endpoint principal de chat. Conecta la solicitud al Orquestador y a la capa desacoplada de LLM.
    """
    orchestrator = get_orchestrator_service()
    result = await orchestrator.process_user_input(payload.message, use_llm=True)
    return ChatResponse(
        response=result.response,
        intent=result.intent,
        agent=result.agent
    )

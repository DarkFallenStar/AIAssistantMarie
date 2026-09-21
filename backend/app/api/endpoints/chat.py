from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.orchestrator import get_orchestrator_service
from app.audio.tts import get_tts_service
from app.core.security import verify_api_bearer_token

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Chat con Asistente / Orquestador Multi-Agente")
async def chat(
    payload: ChatRequest,
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Endpoint principal de chat. Conecta la solicitud al Orquestador y ejecuta Function Calling (Fase 11)
    e integra síntesis de voz TTS (Fase 13).
    """
    orchestrator = get_orchestrator_service()
    result = await orchestrator.process_user_input(payload.message, use_llm=True)

    audio_url = None
    try:
        tts = get_tts_service()
        if result.response and result.response.strip():
            audio_file = tts.synthesize(result.response)
            audio_url = f"/static/audio/tts/{audio_file.name}"
    except Exception as exc:
        print(f"[CHAT] TTS synthesis fallback: {exc}")

    return ChatResponse(
        response=result.response,
        intent=result.intent,
        agent=result.agent,
        tools_executed=result.tools_executed,
        structured_intent=result.structured_intent.model_dump() if result.structured_intent else None,
        audio_url=audio_url
    )

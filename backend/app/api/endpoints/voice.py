from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from app.schemas.voice import VoiceUploadResponse
from app.audio.stt import get_stt_service
from app.audio.tts import get_tts_service
from app.agents.orchestrator import get_orchestrator_service

router = APIRouter()

UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/voice", response_model=VoiceUploadResponse, summary="Captura de Audio y Speech To Text (Fase 6)")
async def upload_voice(file: UploadFile = File(...)):
    """
    Recibe el archivo binario de audio grabado desde la aplicación móvil.
    Convierte el audio a texto (Speech To Text) y lo pasa como entrada al Orquestador.
    Sintetiza la respuesta en audio mediante TTS (Fase 13).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporciono archivo de audio.")
    
    contents = await file.read()
    size_bytes = len(contents)
    
    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="El archivo de audio recibido esta vacio (0 bytes).")
    
    safe_filename = Path(file.filename).name
    save_path = UPLOAD_DIR / safe_filename
    with open(save_path, "wb") as f:
        f.write(contents)
    
    print(f"[VOICE] Audio guardado: {safe_filename} ({size_bytes} bytes, tipo: {file.content_type})")
    
    # 1. Transcripción Speech To Text (STT)
    stt_service = get_stt_service()
    try:
        transcribed_text = stt_service.transcribe(save_path, language="es")
    except Exception as exc:
        print(f"[VOICE] Error en transcripcion STT: {exc}")
        transcribed_text = ""
    
    # 2. Entrada al Orquestador con soporte LLM
    orchestrator = get_orchestrator_service()
    orchestrator_result = await orchestrator.process_user_input(transcribed_text, use_llm=True)

    # 3. Síntesis Text To Speech (TTS)
    audio_url = None
    try:
        tts = get_tts_service()
        if orchestrator_result.response and orchestrator_result.response.strip():
            audio_file = tts.synthesize(orchestrator_result.response)
            audio_url = f"/static/audio/tts/{audio_file.name}"
    except Exception as exc:
        print(f"[VOICE] Error en sintesis TTS: {exc}")
    
    return VoiceUploadResponse(
        status="success",
        filename=safe_filename,
        size_bytes=size_bytes,
        content_type=file.content_type,
        transcribed_text=transcribed_text,
        intent=orchestrator_result.intent,
        message=f"Audio procesado correctamente. Transcripcion: '{transcribed_text}'",
        response=orchestrator_result.response,
        audio_url=audio_url,
    )

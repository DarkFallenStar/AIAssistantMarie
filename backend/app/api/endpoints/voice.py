import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pathlib import Path
from app.schemas.voice import VoiceUploadResponse
from app.audio.stt import get_stt_service
from app.audio.tts import get_tts_service
from app.agents.orchestrator import get_orchestrator_service
from app.core.security import verify_api_bearer_token

router = APIRouter()

UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 25MB maximum upload limit
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".m4a", ".wav", ".mp3", ".aac", ".ogg", ".flac", ".mp4", ".caf"}

@router.post("/voice", response_model=VoiceUploadResponse, summary="Captura de Audio y Speech To Text (Fase 6)")
async def upload_voice(
    file: UploadFile = File(...),
    _authorized: bool = Depends(verify_api_bearer_token)
):
    """
    Recibe el archivo binario de audio grabado desde la aplicación móvil.
    Convierte el audio a texto (Speech To Text) y lo pasa como entrada al Orquestador.
    Sintetiza la respuesta en audio mediante TTS (Fase 13).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó archivo de audio.")
    
    contents = await file.read()
    size_bytes = len(contents)
    
    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="El archivo de audio recibido esta vacio (0 bytes).")
    
    if size_bytes > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE),
            detail=f"El archivo de audio excede el límite permitido de 25MB ({size_bytes} bytes recibidos)."
        )
    
    # Path Traversal prevention & safe filename generation on disk
    original_name = Path(file.filename).name
    raw_ext = Path(file.filename).suffix.lower()
    safe_ext = raw_ext if raw_ext in ALLOWED_AUDIO_EXTENSIONS else ".m4a"
    clean_base = Path(file.filename).stem[:30]
    safe_filename = f"{uuid.uuid4().hex[:8]}_{clean_base}{safe_ext}"
    save_path = UPLOAD_DIR / safe_filename
    with open(save_path, "wb") as f:
        f.write(contents)
    
    print(f"[VOICE] Audio guardado de forma segura: {safe_filename} ({size_bytes} bytes, tipo: {file.content_type})")
    
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
        filename=original_name,
        size_bytes=size_bytes,
        content_type=file.content_type,
        transcribed_text=transcribed_text,
        intent=orchestrator_result.intent,
        message=f"Audio procesado correctamente. Transcripcion: '{transcribed_text}'",
        response=orchestrator_result.response,
        audio_url=audio_url,
    )

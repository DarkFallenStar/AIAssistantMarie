from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from app.audio.tts import get_tts_service, TTS_DIR
from app.core.security import verify_api_bearer_token

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Texto a sintetizar en audio")
    voice: Optional[str] = Field(default="es", max_length=50, description="Código o nombre de voz (ej: 'es')")


class TTSResponse(BaseModel):
    status: str
    audio_url: str
    text: str


@router.post("/tts", summary="Sintetizar texto a audio (Fase 13 - TTS)")
async def text_to_speech(
    request: TTSRequest,
    as_json: bool = Query(False, description="Si es True, devuelve JSON con audio_url"),
    _authorized: bool = Depends(verify_api_bearer_token),
):
    """
    Convierte el texto recibido a un archivo de audio mediante el servicio TTS.
    Por defecto devuelve el archivo binario de audio (.wav).
    Si as_json=True, devuelve un objeto JSON con la URL relativa del archivo generado.
    """
    clean_text = request.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="El texto proporcionado está vacío.")

    try:
        tts_service = get_tts_service()
        audio_path = tts_service.synthesize(clean_text, voice=request.voice)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en la síntesis de audio TTS: {exc}")

    if as_json:
        audio_url = f"/static/audio/tts/{audio_path.name}"
        return TTSResponse(status="success", audio_url=audio_url, text=clean_text)

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=audio_path.name,
    )


@router.get("/tts/{filename}", summary="Obtener archivo de audio generado por TTS")
async def get_tts_audio(filename: str):
    """
    Descarga o reproduce el archivo de audio TTS generado previamente.
    Protegido contra ataques de Directory Traversal.
    """
    safe_name = Path(filename).name
    file_path = (TTS_DIR / safe_name).resolve()
    base_dir = TTS_DIR.resolve()

    if not str(file_path).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail="Acceso denegado: ruta de archivo no permitida.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo de audio no encontrado.")

    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=safe_name,
    )

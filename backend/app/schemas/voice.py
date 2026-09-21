from pydantic import BaseModel
from typing import Optional

class VoiceUploadResponse(BaseModel):
    status: str
    filename: str
    size_bytes: int
    content_type: Optional[str] = None
    transcribed_text: Optional[str] = None
    intent: Optional[str] = None
    message: str
    response: str
    audio_url: Optional[str] = None

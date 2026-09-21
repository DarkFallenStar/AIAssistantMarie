from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
from app.core.config import settings

class BaseSTTService(ABC):
    """
    Abstract interface for Speech To Text services.
    """
    @abstractmethod
    def transcribe(self, audio_path: Union[str, Path], language: Optional[str] = "es") -> str:
        """
        Transcribes the audio file located at audio_path into text.
        """
        pass


class WhisperSTTService(BaseSTTService):
    """
    STT Service implementation using faster-whisper with CTranslate2.
    Utilizes lazy model loading to avoid slowing down FastAPI startup.
    """
    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        self.model_size = model_size or settings.WHISPER_MODEL_SIZE
        self.device = device or settings.WHISPER_DEVICE
        self.compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE
        self._model = None

    def _get_model(self):
        if self._model is None:
            print(f"[STT] Initializing Whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            print(f"[STT] Whisper model '{self.model_size}' ready.")
        return self._model

    def transcribe(self, audio_path: Union[str, Path], language: Optional[str] = "es") -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        print(f"[STT] Starting transcription for {path.name}...")
        model = self._get_model()

        try:
            segments, info = model.transcribe(
                str(path),
                language=language,
                beam_size=5,
                vad_filter=True,
            )
            
            collected_text = []
            for segment in segments:
                text_piece = segment.text.strip()
                if text_piece:
                    collected_text.append(text_piece)

            transcribed = " ".join(collected_text).strip()
            print(f"[STT] Transcription complete (lang={info.language}): '{transcribed}'")
            return transcribed
        except Exception as exc:
            print(f"[STT] Error during transcription: {exc}")
            raise


class MockSTTService(BaseSTTService):
    """
    Deterministic mock STT service for testing and development.
    """
    def __init__(self, canned_response: str = "¿Cuánto dinero me queda disponible para salir este fin de semana?"):
        self.canned_response = canned_response

    def transcribe(self, audio_path: Union[str, Path], language: Optional[str] = "es") -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        print(f"[STT-MOCK] Transcribing {path.name} -> '{self.canned_response}'")
        return self.canned_response


_stt_instance: Optional[BaseSTTService] = None

def get_stt_service() -> BaseSTTService:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = WhisperSTTService()
    return _stt_instance

def set_stt_service(service: Optional[BaseSTTService]):
    """Override STT service (e.g. with MockSTTService for tests)."""
    global _stt_instance
    _stt_instance = service

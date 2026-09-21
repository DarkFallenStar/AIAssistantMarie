from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
import uuid
import wave
import math
import struct
from app.core.config import settings

TTS_DIR = Path("uploads/audio/tts")
TTS_DIR.mkdir(parents=True, exist_ok=True)


class BaseTTSService(ABC):
    """
    Abstract interface for Text To Speech services.
    """
    @abstractmethod
    def synthesize(self, text: str, output_path: Optional[Union[str, Path]] = None, voice: Optional[str] = "es") -> Path:
        """
        Synthesizes given text into an audio file and returns the Path to the generated audio file.
        """
        pass


class MockTTSService(BaseTTSService):
    """
    Deterministic offline TTS service that creates a valid standard .wav file
    with generated audio samples. Useful for testing, offline use, and zero-dependency operation.
    """
    def __init__(self, sample_rate: int = 16000, duration_seconds: float = 0.5):
        self.sample_rate = sample_rate
        self.duration_seconds = duration_seconds

    def synthesize(self, text: str, output_path: Optional[Union[str, Path]] = None, voice: Optional[str] = "es") -> Path:
        if not text or not text.strip():
            raise ValueError("El texto para sintesis de audio no puede estar vacio.")

        if output_path is None:
            file_id = str(uuid.uuid4())
            dest_path = TTS_DIR / f"tts_{file_id}.wav"
        else:
            dest_path = Path(output_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

        num_samples = int(self.sample_rate * self.duration_seconds)
        frequency = 440.0  # standard A4 tone
        amplitude = 16000

        with wave.open(str(dest_path), "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)

            raw_data = bytearray()
            for i in range(num_samples):
                sample = int(amplitude * math.sin(2.0 * math.pi * frequency * (i / self.sample_rate)))
                raw_data.extend(struct.pack("<h", sample))

            wav_file.writeframes(raw_data)

        clean_preview = text[:40].encode("ascii", "replace").decode("ascii")
        print(f"[TTS-MOCK] Synthesized audio for '{clean_preview}...' -> {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return dest_path


_tts_instance: Optional[BaseTTSService] = None


def get_tts_service() -> BaseTTSService:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = MockTTSService()
    return _tts_instance


def set_tts_service(service: Optional[BaseTTSService]):
    """Override TTS service (e.g. for testing)."""
    global _tts_instance
    _tts_instance = service

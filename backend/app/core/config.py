from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_FILES = [
    str(_BACKEND_DIR / ".env"),
    str(_ROOT_DIR / ".env"),
    ".env",
]

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Assistant AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # CORS: Allow all origins by default for mobile development and Tailscale
    CORS_ORIGINS: List[str] = ["*"]
    
    # LLM Settings
    LLM_PROVIDER: str = "dual"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT_SECONDS: float = 25.0
    
    # Google AI Studio (Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_TIMEOUT_SECONDS: float = 25.0
    
    # Supabase / PostgreSQL Database Settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""
    
    # Security and Authentication (Phase 17)
    API_BEARER_TOKEN: str = ""
    BANK_WEBHOOK_SECRET: str = ""
    
    # Speech To Text (Whisper) Settings
    WHISPER_MODEL_SIZE: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Official Email / IMAP Settings (Fase 12)
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_USE_SSL: bool = True
    
    class Config:
        env_file = _ENV_FILES
        case_sensitive = True
        extra = "ignore"

# Global settings singleton (reloaded)
settings = Settings()

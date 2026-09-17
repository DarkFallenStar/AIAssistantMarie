from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Assistant AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS: Allow all origins by default for mobile development and Tailscale
    CORS_ORIGINS: List[str] = ["*"]
    
    # LLM Settings (Modular architecture: Ollama, OpenAI, Gemini, etc.)
    LLM_PROVIDER: str = "ollama"  # "ollama", "gemini", "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

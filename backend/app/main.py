from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import health, chat

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json"
)

# CORS configuration - allows mobile client via local network and Tailscale
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes directly at root level (/health, /chat) as requested
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, tags=["Chat"])

# Also register under /api prefix for API consistency
app.include_router(health.router, prefix="/api", tags=["Health API"])
app.include_router(chat.router, prefix="/api", tags=["Chat API"])

@app.get("/")
async def root():
    return {
        "message": "Personal Assistant AI API",
        "health": "/health",
        "chat": "/chat",
        "docs": "/docs"
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import health, chat, database

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level routes
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(database.router, tags=["Database"])

# Prefixed API routes
app.include_router(health.router, prefix="/api", tags=["Health API"])
app.include_router(chat.router, prefix="/api", tags=["Chat API"])
app.include_router(database.router, prefix="/api", tags=["Database API"])

@app.get("/")
async def root():
    return {
        "message": "Personal Assistant AI API",
        "health": "/health",
        "chat": "/chat",
        "db_status": "/db/status",
        "docs": "/docs"
    }

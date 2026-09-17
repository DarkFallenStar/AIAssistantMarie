from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration - essential for Expo mobile app connecting across network/Tailscale
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])

@app.get("/")
async def root():
    return {
        "message": "Personal Assistant AI API is running",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs"
    }

from app.main import app
from app.core.config import settings
import uvicorn

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT
    )


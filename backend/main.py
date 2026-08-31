from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

load_dotenv()

app = FastAPI(
    title="AI Kubernetes Agent",
    description="AI-powered Kubernetes troubleshooting agent",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.add("logs/app.log", rotation="500 MB")

# Import and include routers
try:
    from api.investigation import router as investigation_router
    app.include_router(investigation_router)
    logger.info("Investigation router included successfully")
except Exception as e:
    logger.error(f"Failed to include investigation router: {e}")

try:
    from api.clusters import router as clusters_router
    app.include_router(clusters_router)
    logger.info("Clusters router included successfully")
except Exception as e:
    logger.error(f"Failed to include clusters router: {e}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-kubernetes-agent"
    }


@app.get("/")
async def root():
    return {
        "message": "AI Kubernetes Agent API",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

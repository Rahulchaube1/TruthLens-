"""TruthLens FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from api.routes.detect import router as detect_router
from api.routes.auth import router as auth_router
from api.routes.history import router as history_router
from ml.model_loader import ModelLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model_loader = ModelLoader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup, release on shutdown."""
    logger.info("Loading ML models...")
    await model_loader.load_all()
    app.state.models = model_loader
    logger.info("Models loaded successfully.")
    yield
    logger.info("Shutting down TruthLens backend.")


app = FastAPI(
    title="TruthLens API",
    description="Real-Time Deepfake & Media Authenticity Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(detect_router, prefix="/api/detect", tags=["detect"])
app.include_router(history_router, prefix="/api/history", tags=["history"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TruthLens API"}

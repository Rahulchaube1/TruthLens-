"""Detection endpoints for video, audio, and image deepfake analysis."""
import base64
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.routes.auth import get_current_user
from ml.video_detector import VideoDetector
from ml.audio_detector import AudioDetector
from ml.image_detector import ImageDetector

router = APIRouter()


# ── Request / Response models ────────────────────────────────────────────────

class VideoDetectRequest(BaseModel):
    url: Optional[str] = None
    frames: Optional[List[str]] = None  # base64-encoded frames


class VideoDetectResponse(BaseModel):
    is_deepfake: bool
    confidence: float
    frame_scores: List[float]
    detection_time_ms: int
    risk_level: str


class AudioDetectRequest(BaseModel):
    audio_base64: str
    duration_seconds: float


class AudioDetectResponse(BaseModel):
    is_cloned: bool
    confidence: float
    voice_artifacts: List[str]
    synthesis_model_guess: str


class ImageDetectRequest(BaseModel):
    image_base64: str
    check_metadata: bool = True


class ImageDetectResponse(BaseModel):
    is_ai_generated: bool
    confidence: float
    gan_artifacts: bool
    metadata_inconsistencies: List[str]
    generator_model_guess: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _risk_level(confidence: float) -> str:
    if confidence < 0.3:
        return "low"
    if confidence < 0.6:
        return "medium"
    if confidence < 0.85:
        return "high"
    return "critical"


def _get_models(request: Request):
    loader = getattr(request.app.state, "models", None)
    if loader is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return loader


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/video", response_model=VideoDetectResponse)
async def detect_video(
    body: VideoDetectRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    loader = _get_models(request)
    if not body.frames and not body.url:
        raise HTTPException(status_code=400, detail="Provide url or frames")

    start = time.monotonic()
    detector: VideoDetector = loader.video_detector
    frame_scores = await detector.analyze(frames_b64=body.frames, url=body.url)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    deepfake_frames = sum(1 for s in frame_scores if s > 0.7)
    is_deepfake = (deepfake_frames / max(len(frame_scores), 1)) > 0.4
    confidence = float(sum(frame_scores) / max(len(frame_scores), 1))

    return VideoDetectResponse(
        is_deepfake=is_deepfake,
        confidence=round(confidence, 4),
        frame_scores=[round(s, 4) for s in frame_scores],
        detection_time_ms=elapsed_ms,
        risk_level=_risk_level(confidence),
    )


@router.post("/audio", response_model=AudioDetectResponse)
async def detect_audio(
    body: AudioDetectRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    loader = _get_models(request)
    detector: AudioDetector = loader.audio_detector
    result = await detector.analyze(audio_b64=body.audio_base64, duration=body.duration_seconds)
    return AudioDetectResponse(**result)


@router.post("/image", response_model=ImageDetectResponse)
async def detect_image(
    body: ImageDetectRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    loader = _get_models(request)
    detector: ImageDetector = loader.image_detector
    result = await detector.analyze(image_b64=body.image_base64, check_metadata=body.check_metadata)
    return ImageDetectResponse(**result)

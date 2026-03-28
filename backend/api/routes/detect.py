"""Detection endpoints for video, audio, image, text, and batch deepfake analysis."""
import base64
import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.routes.auth import get_current_user
from ml.video_detector import VideoDetector
from ml.audio_detector import AudioDetector
from ml.image_detector import ImageDetector
from ml.text_detector import TextDetector

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


class TextDetectRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to analyse for AI generation")


class TextDetectResponse(BaseModel):
    is_ai_generated: bool
    confidence: float
    ai_artifacts: List[str]
    generator_model_guess: str
    word_count: int
    sentence_count: int
    risk_level: str


class BatchDetectItem(BaseModel):
    type: Literal["video", "audio", "image", "text"]
    # video/image payload
    url: Optional[str] = None
    frames: Optional[List[str]] = None
    image_base64: Optional[str] = None
    check_metadata: bool = True
    # audio payload
    audio_base64: Optional[str] = None
    duration_seconds: Optional[float] = None
    # text payload
    text: Optional[str] = None


class BatchDetectRequest(BaseModel):
    items: List[BatchDetectItem] = Field(..., min_length=1, max_length=10)


class BatchDetectResult(BaseModel):
    index: int
    type: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    detection_time_ms: int


class BatchDetectResponse(BaseModel):
    results: List[BatchDetectResult]
    total: int
    succeeded: int
    failed: int
    total_time_ms: int


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


@router.post("/text", response_model=TextDetectResponse)
async def detect_text(
    body: TextDetectRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    """Detect AI-generated text (GPT-4, Claude, Gemini, Llama, etc.)."""
    loader = _get_models(request)
    detector: TextDetector = loader.text_detector
    result = await detector.analyze(text=body.text)
    return TextDetectResponse(
        **result,
        risk_level=_risk_level(result["confidence"]),
    )


@router.post("/batch", response_model=BatchDetectResponse)
async def detect_batch(
    body: BatchDetectRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    """Analyse multiple media items in a single request (max 10 items)."""
    loader = _get_models(request)
    batch_start = time.monotonic()
    results: List[BatchDetectResult] = []

    for idx, item in enumerate(body.items):
        item_start = time.monotonic()
        try:
            if item.type == "video":
                if not item.frames and not item.url:
                    raise ValueError("Provide url or frames for video item")
                detector: VideoDetector = loader.video_detector
                frame_scores = await detector.analyze(frames_b64=item.frames, url=item.url)
                deepfake_frames = sum(1 for s in frame_scores if s > 0.7)
                is_deepfake = (deepfake_frames / max(len(frame_scores), 1)) > 0.4
                confidence = float(sum(frame_scores) / max(len(frame_scores), 1))
                result_data = {
                    "is_deepfake": is_deepfake,
                    "confidence": round(confidence, 4),
                    "frame_scores": [round(s, 4) for s in frame_scores],
                    "risk_level": _risk_level(confidence),
                }
            elif item.type == "audio":
                if not item.audio_base64:
                    raise ValueError("Provide audio_base64 for audio item")
                audio_detector: AudioDetector = loader.audio_detector
                result_data = await audio_detector.analyze(
                    audio_b64=item.audio_base64,
                    duration=item.duration_seconds or 0.0,
                )
            elif item.type == "image":
                if not item.image_base64:
                    raise ValueError("Provide image_base64 for image item")
                img_detector: ImageDetector = loader.image_detector
                result_data = await img_detector.analyze(
                    image_b64=item.image_base64,
                    check_metadata=item.check_metadata,
                )
            elif item.type == "text":
                if not item.text:
                    raise ValueError("Provide text for text item")
                txt_detector: TextDetector = loader.text_detector
                result_data = await txt_detector.analyze(text=item.text)
                result_data["risk_level"] = _risk_level(result_data["confidence"])
            else:
                raise ValueError(f"Unsupported item type: {item.type}")

            results.append(BatchDetectResult(
                index=idx,
                type=item.type,
                success=True,
                result=result_data,
                detection_time_ms=int((time.monotonic() - item_start) * 1000),
            ))
        except Exception as exc:
            results.append(BatchDetectResult(
                index=idx,
                type=item.type,
                success=False,
                error=str(exc),
                detection_time_ms=int((time.monotonic() - item_start) * 1000),
            ))

    succeeded = sum(1 for r in results if r.success)
    return BatchDetectResponse(
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        total_time_ms=int((time.monotonic() - batch_start) * 1000),
    )

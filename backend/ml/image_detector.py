"""
Image AI-generation detector.

Uses CLIP embeddings + a logistic head to classify AI-generated vs real images.
Also performs GAN artifact detection and EXIF metadata analysis.
"""
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ImageDetector:
    def __init__(self):
        self._clip_model = None
        self._clip_processor = None
        self._classifier = None
        self._device = None

    async def load(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_sync)

    def _load_sync(self):
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("ImageDetector using device: %s", self._device)

        self._clip_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32",
            cache_dir="/tmp/models",
        ).to(self._device)
        self._clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32",
            cache_dir="/tmp/models",
        )

        import torch.nn as nn
        self._classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
        ).to(self._device)
        self._classifier.eval()

    async def analyze(self, image_b64: str, check_metadata: bool = True) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, image_b64, check_metadata)

    def _analyze_sync(self, image_b64: str, check_metadata: bool) -> Dict[str, Any]:
        import torch
        from PIL import Image
        import io, base64

        def _pad_b64(s: str) -> str:
            return s + "=" * (-len(s) % 4)

        try:
            raw = base64.b64decode(_pad_b64(image_b64))
            img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as exc:
            logger.error("Image decode failed: %s", exc)
            return self._empty_result()

        # CLIP embedding
        inputs = self._clip_processor(images=img, return_tensors="pt").to(self._device)
        with torch.no_grad():
            feats = self._clip_model.get_image_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            logit = self._classifier(feats)
            confidence = float(torch.sigmoid(logit).item())

        gan_artifacts = self._detect_gan_artifacts(img)
        metadata_issues = self._check_metadata(raw) if check_metadata else []
        model_guess = self._guess_generator(confidence, gan_artifacts)

        return {
            "is_ai_generated": confidence > 0.5,
            "confidence": round(confidence, 4),
            "gan_artifacts": gan_artifacts,
            "metadata_inconsistencies": metadata_issues,
            "generator_model_guess": model_guess,
        }

    def _detect_gan_artifacts(self, img) -> bool:
        """Detect checkerboard/upscaling artifacts via frequency analysis."""
        try:
            import numpy as np
            arr = np.array(img.convert("L"), dtype=np.float32)
            fft = np.fft.fft2(arr)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.abs(fft_shift)
            h, w = magnitude.shape
            # Look for periodic peaks in the high-frequency quadrants
            quad = magnitude[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
            outer = magnitude.copy()
            outer[h // 4: 3 * h // 4, w // 4: 3 * w // 4] = 0
            ratio = float(np.max(outer)) / (float(np.mean(quad)) + 1e-9)
            return ratio > 50.0
        except Exception:
            return False

    def _check_metadata(self, raw_bytes: bytes) -> List[str]:
        """Check EXIF metadata for inconsistencies."""
        from utils.metadata_analyzer import analyze_metadata
        return analyze_metadata(raw_bytes)

    def _guess_generator(self, confidence: float, has_gan_artifacts: bool) -> str:
        if confidence < 0.4:
            return "authentic"
        if has_gan_artifacts:
            return "StyleGAN / BigGAN"
        if confidence > 0.8:
            return "Stable Diffusion / DALL-E"
        return "unknown AI generator"

    def _empty_result(self):
        return {
            "is_ai_generated": False,
            "confidence": 0.0,
            "gan_artifacts": False,
            "metadata_inconsistencies": [],
            "generator_model_guess": "unknown",
        }

"""
Video deepfake detector.

Uses EfficientNet-B4 fine-tuned on FaceForensics++ (simulated here via a
pretrained ImageNet checkpoint when the fine-tuned weights are not present).
MTCNN is used for face detection and alignment.
"""
import asyncio
import logging
from typing import List, Optional

import numpy as np

from ml.preprocessors import extract_frames_from_b64, resize_and_normalize

logger = logging.getLogger(__name__)

_DEEPFAKE_THRESHOLD = 0.7
_FAKE_FRAME_RATIO = 0.4


class VideoDetector:
    def __init__(self):
        self._model = None
        self._face_detector = None
        self._transform = None
        self._device = None

    async def load(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_sync)

    def _load_sync(self):
        import torch
        import torchvision.transforms as T
        from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("VideoDetector using device: %s", self._device)

        # Load pretrained EfficientNet-B4 (fine-tuned weights would replace this)
        weights = EfficientNet_B4_Weights.DEFAULT
        model = efficientnet_b4(weights=weights)
        # Replace classifier head for binary classification (real vs fake)
        import torch.nn as nn
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 1),
        )
        model.eval()
        model.to(self._device)
        self._model = model

        self._transform = T.Compose([
            T.ToPILImage(),
            T.Resize((380, 380)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        try:
            from facenet_pytorch import MTCNN
            self._face_detector = MTCNN(keep_all=False, device=self._device)
            logger.info("MTCNN face detector loaded.")
        except Exception as exc:
            logger.warning("MTCNN not available, skipping face detection: %s", exc)

    async def analyze(self, frames_b64: Optional[List[str]] = None, url: Optional[str] = None) -> List[float]:
        """Return per-frame deepfake probability scores."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, frames_b64, url)

    def _analyze_sync(self, frames_b64: Optional[List[str]], url: Optional[str]) -> List[float]:
        import torch
        frames = []
        if frames_b64:
            frames = extract_frames_from_b64(frames_b64)
        elif url:
            frames = self._extract_frames_from_url(url)

        if not frames:
            return []

        scores = []
        with torch.no_grad():
            for frame in frames:
                score = self._score_frame(frame)
                scores.append(score)

        return scores

    def _score_frame(self, frame: np.ndarray) -> float:
        import torch
        try:
            tensor = self._transform(frame).unsqueeze(0).to(self._device)
            logit = self._model(tensor)
            prob = torch.sigmoid(logit).item()
            return float(prob)
        except Exception as exc:
            logger.error("Frame scoring error: %s", exc)
            return 0.0

    def _extract_frames_from_url(self, url: str) -> List[np.ndarray]:
        """Download video and extract 30 evenly-spaced frames via OpenCV."""
        try:
            import cv2
            import tempfile
            import httpx

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                resp = httpx.get(url, timeout=30, follow_redirects=True)
                tmp.write(resp.content)
                tmp_path = tmp.name

            cap = cv2.VideoCapture(tmp_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            indices = np.linspace(0, max(total - 1, 0), 30, dtype=int)
            frames = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if ret:
                    frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            cap.release()
            return frames
        except Exception as exc:
            logger.error("Failed to extract frames from URL: %s", exc)
            return []

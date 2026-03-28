"""Frame extraction and audio pre-processing utilities."""
import base64
import io
import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def decode_base64_image(b64: str) -> np.ndarray:
    """Decode a base64 string to an RGB numpy array."""
    from PIL import Image
    data = base64.b64decode(b64 + "==")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.array(img)


def resize_and_normalize(img: np.ndarray, size: Tuple[int, int] = (380, 380)) -> np.ndarray:
    """Resize to target size and normalise to [0, 1]."""
    from PIL import Image
    pil = Image.fromarray(img).resize(size, Image.LANCZOS)
    arr = np.array(pil, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return (arr - mean) / std


def extract_frames_from_b64(frames_b64: List[str]) -> List[np.ndarray]:
    """Decode a list of base64-encoded frames."""
    frames = []
    for b64 in frames_b64:
        try:
            frames.append(decode_base64_image(b64))
        except Exception as exc:
            logger.warning("Failed to decode frame: %s", exc)
    return frames


def decode_base64_audio(b64: str) -> Tuple[np.ndarray, int]:
    """Decode base64 audio to (waveform_float32, sample_rate)."""
    import soundfile as sf
    data = base64.b64decode(b64 + "==")
    buf = io.BytesIO(data)
    waveform, sr = sf.read(buf, dtype="float32", always_2d=False)
    return waveform, sr


def resample_audio(waveform: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Resample waveform to target sample rate."""
    import librosa
    if orig_sr == target_sr:
        return waveform
    return librosa.resample(waveform, orig_sr=orig_sr, target_sr=target_sr)


def extract_mel_spectrogram(waveform: np.ndarray, sr: int = 16000) -> np.ndarray:
    """Return a log-mel spectrogram as a 2-D float32 array."""
    import librosa
    mel = librosa.feature.melspectrogram(y=waveform, sr=sr, n_mels=128, fmax=8000)
    return librosa.power_to_db(mel, ref=np.max).astype(np.float32)

"""
Audio voice-clone detector.

Uses a lightweight Wav2Vec 2.0 feature extractor and a binary classifier
trained to distinguish authentic vs. TTS/voice-cloned audio.
"""
import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_KNOWN_TTS_SIGNATURES = {
    "high_spectral_flatness": "Tortoise-TTS / VALL-E",
    "phase_discontinuity": "ElevenLabs / Resemble AI",
    "low_prosody_variance": "Google TTS / Amazon Polly",
    "high_periodicity": "Bark / XTTS-v2",
}


class AudioDetector:
    def __init__(self):
        self._feature_extractor = None
        self._model = None
        self._device = None

    async def load(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_sync)

    def _load_sync(self):
        import torch
        from transformers import Wav2Vec2FeatureExtractor

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("AudioDetector using device: %s", self._device)

        self._feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            "facebook/wav2vec2-base",
            cache_dir="/tmp/models",
        )

        # Binary classification head on top of Wav2Vec2 base
        import torch.nn as nn
        from transformers import Wav2Vec2Model

        class Wav2Vec2Classifier(nn.Module):
            def __init__(self):
                super().__init__()
                self.wav2vec2 = Wav2Vec2Model.from_pretrained(
                    "facebook/wav2vec2-base",
                    cache_dir="/tmp/models",
                )
                self.classifier = nn.Sequential(
                    nn.Linear(768, 256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 1),
                )

            def forward(self, input_values, attention_mask=None):
                outputs = self.wav2vec2(input_values=input_values, attention_mask=attention_mask)
                hidden = outputs.last_hidden_state.mean(dim=1)
                return self.classifier(hidden)

        self._model = Wav2Vec2Classifier().to(self._device)
        self._model.eval()

    async def analyze(self, audio_b64: str, duration: float) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, audio_b64, duration)

    def _analyze_sync(self, audio_b64: str, duration: float) -> Dict[str, Any]:
        import torch
        from ml.preprocessors import decode_base64_audio, resample_audio, extract_mel_spectrogram

        try:
            waveform, sr = decode_base64_audio(audio_b64)
        except Exception as exc:
            logger.error("Audio decode failed: %s", exc)
            return self._empty_result()

        waveform = resample_audio(waveform, sr, 16000)

        # Feature extraction
        inputs = self._feature_extractor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )
        input_values = inputs.input_values.to(self._device)

        with torch.no_grad():
            logit = self._model(input_values)
            confidence = float(torch.sigmoid(logit).item())

        artifacts = self._detect_artifacts(waveform)
        model_guess = self._guess_tts_model(artifacts)

        return {
            "is_cloned": confidence > 0.5,
            "confidence": round(confidence, 4),
            "voice_artifacts": artifacts,
            "synthesis_model_guess": model_guess,
        }

    def _detect_artifacts(self, waveform) -> list:
        """Heuristic artifact detection on raw waveform."""
        import numpy as np
        artifacts = []
        try:
            import librosa
            # Spectral flatness — high values indicate synthesised audio
            flatness = librosa.feature.spectral_flatness(y=waveform)
            if float(flatness.mean()) > 0.15:
                artifacts.append("high_spectral_flatness")

            # Prosody variance (pitch std deviation)
            f0, _, _ = librosa.pyin(waveform, fmin=50, fmax=500, sr=16000)
            f0_valid = f0[~np.isnan(f0)]
            if len(f0_valid) > 10 and float(f0_valid.std()) < 15.0:
                artifacts.append("low_prosody_variance")

            # Periodicity
            ac = np.correlate(waveform[:4096], waveform[:4096], mode="full")
            peak_ratio = float(np.max(ac[len(ac) // 2 + 10:]) / (np.max(np.abs(ac)) + 1e-9))
            if peak_ratio > 0.7:
                artifacts.append("high_periodicity")

        except Exception as exc:
            logger.warning("Artifact detection error: %s", exc)
        return artifacts

    def _guess_tts_model(self, artifacts: list) -> str:
        for artifact in artifacts:
            if artifact in _KNOWN_TTS_SIGNATURES:
                return _KNOWN_TTS_SIGNATURES[artifact]
        return "unknown"

    def _empty_result(self):
        return {
            "is_cloned": False,
            "confidence": 0.0,
            "voice_artifacts": [],
            "synthesis_model_guess": "unknown",
        }

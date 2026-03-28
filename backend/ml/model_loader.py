"""Load and manage all ML models."""
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """Lazily initialises all detectors on first async load."""

    def __init__(self):
        self.video_detector = None
        self.audio_detector = None
        self.image_detector = None

    async def load_all(self):
        from ml.video_detector import VideoDetector
        from ml.audio_detector import AudioDetector
        from ml.image_detector import ImageDetector

        logger.info("Initialising VideoDetector…")
        self.video_detector = VideoDetector()
        await self.video_detector.load()

        logger.info("Initialising AudioDetector…")
        self.audio_detector = AudioDetector()
        await self.audio_detector.load()

        logger.info("Initialising ImageDetector…")
        self.image_detector = ImageDetector()
        await self.image_detector.load()

        logger.info("All models ready.")

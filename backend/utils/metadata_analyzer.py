"""EXIF and C2PA metadata analysis utilities."""
import logging
from typing import List

logger = logging.getLogger(__name__)

_EXPECTED_EXIF_TAGS = {
    "Make", "Model", "DateTime", "Software",
    "GPSInfo", "ExifIFD",
}


def analyze_metadata(raw_bytes: bytes) -> List[str]:
    """Return a list of metadata inconsistency descriptions."""
    issues = []
    try:
        from PIL import Image, ExifTags
        import io

        img = Image.open(io.BytesIO(raw_bytes))
        exif_data = img._getexif()

        if exif_data is None:
            issues.append("No EXIF metadata found — possible AI generation or stripping")
            return issues

        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}

        # Check for common inconsistencies
        if "Software" in tags and any(
            kw in str(tags["Software"]).lower()
            for kw in ("photoshop", "gimp", "stable diffusion", "midjourney", "dall-e")
        ):
            issues.append(f"Software tag indicates editing: {tags['Software']}")

        if "Make" not in tags and "Model" not in tags:
            issues.append("Missing camera Make/Model — possible AI generation")

        if "DateTime" not in tags and "DateTimeOriginal" not in tags:
            issues.append("Missing DateTime — metadata may have been stripped")

        # Check for future dates or obviously invalid timestamps
        if "DateTime" in tags:
            try:
                from datetime import datetime
                dt = datetime.strptime(str(tags["DateTime"]), "%Y:%m:%d %H:%M:%S")
                if dt.year > 2030:
                    issues.append(f"Suspicious future date in EXIF: {dt}")
            except ValueError:
                issues.append("Malformed DateTime in EXIF")

    except Exception as exc:
        logger.warning("Metadata analysis error: %s", exc)
        issues.append(f"Metadata analysis failed: {exc}")

    return issues

"""
Media file discovery and thumbnail generation.
Thumbnails are stored in data/thumbnails/ keyed by relative path + mtime.
"""

import hashlib
import logging
from pathlib import Path

from config.settings import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    PHOTOS_DIR,
    STATIC_DIR,
    THUMBNAILS_DIR,
    THUMBNAIL_HEIGHT,
    THUMBNAIL_QUALITY,
    THUMBNAIL_WIDTH,
    VIDEO_EXTENSIONS,
)

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageService:
    def list_media(self) -> list[dict]:
        """Return sorted list of all media files under PHOTOS_DIR."""
        if not PHOTOS_DIR.exists():
            return []
        items = []
        for path in sorted(PHOTOS_DIR.rglob("*")):
            if path.suffix.lower() in MEDIA_EXTENSIONS:
                rel = path.relative_to(STATIC_DIR).as_posix()
                items.append({
                    "path": rel,
                    "type": "video" if path.suffix.lower() in VIDEO_EXTENSIONS else "image",
                    "name": path.name,
                })
        return items

    def get_thumbnail(self, rel_path: str) -> tuple[bool, str]:
        """
        Return (success, thumbnail_relative_path).
        Generates thumbnail if not cached or source was modified.
        """
        if not PIL_AVAILABLE:
            return False, rel_path

        src = STATIC_DIR / rel_path
        if not src.exists() or src.suffix.lower() not in IMAGE_EXTENSIONS:
            return False, rel_path

        mtime = int(src.stat().st_mtime)
        key = hashlib.md5(f"{rel_path}{mtime}".encode()).hexdigest()
        thumb_path = THUMBNAILS_DIR / f"{key}.jpg"

        if thumb_path.exists():
            return True, thumb_path.relative_to(STATIC_DIR).as_posix()

        try:
            THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
                img.save(thumb_path, "JPEG", quality=THUMBNAIL_QUALITY, optimize=True)
            return True, thumb_path.relative_to(STATIC_DIR).as_posix()
        except Exception as e:
            logger.error("Thumbnail generation failed for %s: %s", rel_path, e)
            return False, rel_path

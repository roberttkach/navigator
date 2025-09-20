import os
from typing import Final

TEXT_MAX: Final = 4096
CAPTION_MAX: Final = 1024
ALBUM_MIN: Final = 2
ALBUM_MAX: Final = 10
ALBUM_MIXED_ALLOWED: Final = {"photo", "video"}
# Если True: любое присутствие thumb в extra при partial-edit альбомов триггерит EDIT_MEDIA.
DETECT_THUMB_CHANGE: bool = os.getenv("NAV_DETECT_THUMB_CHANGE", "0").lower() in {"1", "true", "yes"}

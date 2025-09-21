import warnings
from typing import Final

__all__ = ["TextLimit", "CaptionLimit", "AlbumFloor", "AlbumCeiling", "AlbumBlend", "ThumbWatch"]

TextLimit: Final = 4096
CaptionLimit: Final = 1024
AlbumFloor: Final = 2
AlbumCeiling: Final = 10
AlbumBlend: Final = {"photo", "video"}
ThumbWatch: Final[bool] = False

_DEPRECATED = {
    "TEXT_MAX": TextLimit,
    "CAPTION_MAX": CaptionLimit,
    "ALBUM_MIN": AlbumFloor,
    "ALBUM_MAX": AlbumCeiling,
    "ALBUM_MIXED_ALLOWED": AlbumBlend,
    "DETECT_THUMB_CHANGE": ThumbWatch,
}


def __getattr__(name: str):
    if name in _DEPRECATED:
        warnings.warn(f"{name} is deprecated; use the new single-word constant", DeprecationWarning, stacklevel=2)
        return _DEPRECATED[name]
    raise AttributeError(f"module 'domain.constants' has no attribute {name!r}")

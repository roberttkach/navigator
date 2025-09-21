from typing import Final

__all__ = ["TextLimit", "CaptionLimit", "AlbumFloor", "AlbumCeiling", "AlbumBlend"]

TextLimit: Final = 4096
CaptionLimit: Final = 1024
AlbumFloor: Final = 2
AlbumCeiling: Final = 10
AlbumBlend: Final = {"photo", "video"}


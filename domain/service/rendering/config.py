from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderingConfig:
    detect_thumb_change: bool = False


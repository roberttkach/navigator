from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderingConfig:
    thumb_watch: bool = False


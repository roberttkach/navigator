from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderingConfig:
    thumbguard: bool = False


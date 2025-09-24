from __future__ import annotations

from functools import lru_cache
from typing import Set

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    history_limit: int = Field(18, ge=1, env="NAV_HISTORY_LIMIT")
    chunk: int = Field(100, ge=1, le=100, env="NAV_CHUNK")
    truncate: bool = Field(False, env="NAV_TRUNCATE")
    strictpath: bool = Field(True, env="NAV_STRICT_INLINE_MEDIA_PATH")
    thumbguard: bool = Field(False, env="NAV_DETECT_THUMB_CHANGE")
    redaction: str = Field("safe", env="NAV_LOG_REDACTION")
    text_limit: int = Field(4096, ge=1, env="NAV_TEXT_LIMIT")
    caption_limit: int = Field(1024, ge=1, env="NAV_CAPTION_LIMIT")
    album_floor: int = Field(2, ge=1, env="NAV_ALBUM_FLOOR")
    album_ceiling: int = Field(10, ge=1, env="NAV_ALBUM_CEILING")
    album_blend: str = Field("photo,video", env="NAV_ALBUM_BLEND")
    delete_delay_ms: int = Field(50, ge=0, env="NAV_DELETE_DELAY_MS")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def album_blend_set(self) -> Set[str]:
        return {item.strip() for item in self.album_blend.split(",") if item.strip()}

    @property
    def delete_delay(self) -> float:
        return float(self.delete_delay_ms) / 1000.0


@lru_cache(maxsize=1)
def load() -> Settings:
    return Settings()


__all__ = ["Settings", "load"]

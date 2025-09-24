from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, Set

from pydantic import Field

try:  # pragma: no cover - preferred path when pydantic-settings is available
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _HAS_SETTINGS = True
except ImportError:  # pragma: no cover - minimal fallback for plain pydantic installs
    from pydantic import BaseModel, ConfigDict

    class BaseSettings(BaseModel):  # type: ignore[misc]
        """Simplified settings base that accepts keyword overrides only."""

        model_config = ConfigDict(extra="ignore")

    SettingsConfigDict = ConfigDict  # type: ignore[misc]
    _HAS_SETTINGS = False


_ENV_MAPPING: Dict[str, str] = {
    "history_limit": "NAV_HISTORY_LIMIT",
    "chunk": "NAV_CHUNK",
    "truncate": "NAV_TRUNCATE",
    "strictpath": "NAV_STRICT_INLINE_MEDIA_PATH",
    "thumbguard": "NAV_DETECT_THUMB_CHANGE",
    "redaction": "NAV_LOG_REDACTION",
    "text_limit": "NAV_TEXT_LIMIT",
    "caption_limit": "NAV_CAPTION_LIMIT",
    "album_floor": "NAV_ALBUM_FLOOR",
    "album_ceiling": "NAV_ALBUM_CEILING",
    "album_blend": "NAV_ALBUM_BLEND",
    "delete_delay_ms": "NAV_DELETE_DELAY_MS",
}


def _environment_overrides() -> Dict[str, str]:
    values: Dict[str, str] = {}
    for field, env_key in _ENV_MAPPING.items():
        raw = os.getenv(env_key)
        if raw is not None:
            values[field] = raw
    return values


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    history_limit: int = Field(18, ge=1)
    chunk: int = Field(100, ge=1, le=100)
    truncate: bool = Field(False)
    strictpath: bool = Field(True)
    thumbguard: bool = Field(False)
    redaction: str = Field("safe")
    text_limit: int = Field(4096, ge=1)
    caption_limit: int = Field(1024, ge=1)
    album_floor: int = Field(2, ge=1)
    album_ceiling: int = Field(10, ge=1)
    album_blend: str = Field("photo,video")
    delete_delay_ms: int = Field(50, ge=0)

    @property
    def album_blend_set(self) -> Set[str]:
        return {item.strip() for item in self.album_blend.split(",") if item.strip()}

    @property
    def delete_delay(self) -> float:
        return float(self.delete_delay_ms) / 1000.0


@lru_cache(maxsize=1)
def load() -> Settings:
    if _HAS_SETTINGS:
        return Settings()
    return Settings(**_environment_overrides())


__all__ = ["Settings", "load"]

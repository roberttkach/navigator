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
    "historylimit": "NAV_HISTORY_LIMIT",
    "chunk": "NAV_CHUNK",
    "truncate": "NAV_TRUNCATE",
    "strictpath": "NAV_STRICT_INLINE_MEDIA_PATH",
    "thumbguard": "NAV_DETECT_THUMB_CHANGE",
    "redaction": "NAV_LOG_REDACTION",
    "textlimit": "NAV_TEXT_LIMIT",
    "captionlimit": "NAV_CAPTION_LIMIT",
    "groupmin": "NAV_ALBUM_FLOOR",
    "groupmax": "NAV_ALBUM_CEILING",
    "mixcodes": "NAV_ALBUM_BLEND",
    "deletepausems": "NAV_DELETE_DELAY_MS",
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

    historylimit: int = Field(18, ge=1)
    chunk: int = Field(100, ge=1, le=100)
    truncate: bool = Field(False)
    strictpath: bool = Field(True)
    thumbguard: bool = Field(False)
    redaction: str = Field("safe")
    textlimit: int = Field(4096, ge=1)
    captionlimit: int = Field(1024, ge=1)
    groupmin: int = Field(2, ge=1)
    groupmax: int = Field(10, ge=1)
    mixcodes: str = Field("photo,video")
    deletepausems: int = Field(50, ge=0)

    @property
    def mixset(self) -> Set[str]:
        return {item.strip() for item in self.mixcodes.split(",") if item.strip()}

    @property
    def deletepause(self) -> float:
        return float(self.deletepausems) / 1000.0


@lru_cache(maxsize=1)
def load() -> Settings:
    if _HAS_SETTINGS:
        return Settings()
    return Settings(**_environment_overrides())


__all__ = ["Settings", "load"]

from __future__ import annotations

from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Set


def _alias(field: str, env: str) -> AliasChoices:
    """Build a validation alias accepting both *field* and *env* names."""

    return AliasChoices(field, env)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    historylimit: int = Field(18, ge=1, validation_alias=_alias("historylimit", "NAV_HISTORY_LIMIT"))
    chunk: int = Field(100, ge=1, le=100, validation_alias=_alias("chunk", "NAV_CHUNK"))
    truncate: bool = Field(False, validation_alias=_alias("truncate", "NAV_TRUNCATE"))
    strictpath: bool = Field(
        True,
        validation_alias=_alias("strictpath", "NAV_STRICT_INLINE_MEDIA_PATH"),
    )
    thumbguard: bool = Field(
        False,
        validation_alias=_alias("thumbguard", "NAV_DETECT_THUMB_CHANGE"),
    )
    redaction: str = Field("safe", validation_alias=_alias("redaction", "NAV_LOG_REDACTION"))
    textlimit: int = Field(4096, ge=1, validation_alias=_alias("textlimit", "NAV_TEXT_LIMIT"))
    captionlimit: int = Field(
        1024,
        ge=1,
        validation_alias=_alias("captionlimit", "NAV_CAPTION_LIMIT"),
    )
    groupmin: int = Field(2, ge=1, validation_alias=_alias("groupmin", "NAV_ALBUM_FLOOR"))
    groupmax: int = Field(10, ge=1, validation_alias=_alias("groupmax", "NAV_ALBUM_CEILING"))
    mixcodes: str = Field("photo,video", validation_alias=_alias("mixcodes", "NAV_ALBUM_BLEND"))
    deletepausems: int = Field(
        50,
        ge=0,
        validation_alias=_alias("deletepausems", "NAV_DELETE_DELAY_MS"),
    )

    @property
    def mixset(self) -> Set[str]:
        return {item.strip() for item in self.mixcodes.split(",") if item.strip()}

    @property
    def deletepause(self) -> float:
        return float(self.deletepausems) / 1000.0


@lru_cache(maxsize=1)
def load() -> Settings:
    return Settings()


__all__ = ["Settings", "load"]

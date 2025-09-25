from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Mapping, Set

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


_ENV_FILE = Path(".env")

_ALIASES: Dict[str, str] = {
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


def _alias(field: str) -> AliasChoices:
    """Build a validation alias accepting both *field* and *env* names."""

    return AliasChoices(field, _ALIASES[field])


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    historylimit: int = Field(18, ge=1, validation_alias=_alias("historylimit"))
    chunk: int = Field(100, ge=1, le=100, validation_alias=_alias("chunk"))
    truncate: bool = Field(False, validation_alias=_alias("truncate"))
    strictpath: bool = Field(
        True,
        validation_alias=_alias("strictpath"),
    )
    thumbguard: bool = Field(
        False,
        validation_alias=_alias("thumbguard"),
    )
    redaction: str = Field("safe", validation_alias=_alias("redaction"))
    textlimit: int = Field(4096, ge=1, validation_alias=_alias("textlimit"))
    captionlimit: int = Field(
        1024,
        ge=1,
        validation_alias=_alias("captionlimit"),
    )
    groupmin: int = Field(2, ge=1, validation_alias=_alias("groupmin"))
    groupmax: int = Field(10, ge=1, validation_alias=_alias("groupmax"))
    mixcodes: str = Field("photo,video", validation_alias=_alias("mixcodes"))
    deletepausems: int = Field(
        50,
        ge=0,
        validation_alias=_alias("deletepausems"),
    )

    @property
    def mixset(self) -> Set[str]:
        return {item.strip() for item in self.mixcodes.split(",") if item.strip()}

    @property
    def deletepause(self) -> float:
        return float(self.deletepausems) / 1000.0


def _read_env_file(path: Path) -> Dict[str, str]:
    if not path.exists() or not path.is_file():
        return {}

    data: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.strip()
        if not content or content.startswith("#"):
            continue
        if content.lower().startswith("export "):
            content = content[7:].lstrip()
        if "=" not in content:
            continue
        key, value = content.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            data[key] = value
    return data


def _merge_sources(*sources: Iterable[Mapping[str, str]]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for source in sources:
        for key, value in source.items():
            merged[key] = value
    return merged


def _prepare_payload(raw: Mapping[str, str]) -> Dict[str, str]:
    lowered = {key.lower(): value for key, value in raw.items()}
    payload: Dict[str, str] = {}
    for field, env_name in _ALIASES.items():
        for candidate in (field, env_name):
            value = lowered.get(candidate.lower())
            if value is not None:
                payload[field] = value
                break
    return payload


@lru_cache(maxsize=1)
def load() -> Settings:
    env_file = _read_env_file(_ENV_FILE)
    env_vars: Dict[str, str] = _merge_sources(env_file, os.environ)
    payload = _prepare_payload(env_vars)
    return Settings.model_validate(payload)


__all__ = ["Settings", "load"]

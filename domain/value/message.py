from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scope:
    chat: int | None
    lang: str | None = None
    inline: str | None = None
    business: str | None = None
    category: str | None = None
    topic: int | None = None
    thread: int | None = None

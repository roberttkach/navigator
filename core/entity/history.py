from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .markup import Markup
from .media import MediaItem

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Message:
    id: int
    text: str | None
    media: MediaItem | None
    group: list[MediaItem] | None
    markup: Markup | None
    preview: "Preview" | None = None
    extra: dict[str, Any] | None = None
    extras: list[int] = field(default_factory=list)
    inline: str | None = None
    automated: bool = True
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Entry:
    state: str | None
    view: str | None
    messages: list[Message]
    root: bool = False

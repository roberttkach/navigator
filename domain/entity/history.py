from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .markup import Markup
from .media import MediaItem

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Msg:
    id: int
    text: str | None
    media: MediaItem | None  # В истории path = Telegram file_id
    group: list[MediaItem] | None  # В истории path = Telegram file_id
    markup: Markup | None
    preview: "Preview" | None = None
    extra: dict[str, Any] | None = None
    extras: list[int] = field(default_factory=list)
    inline: str | None = None  # inline_message_id, если есть
    automated: bool = True
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Entry:
    state: str | None
    view: str | None
    messages: list[Msg]
    root: bool = False

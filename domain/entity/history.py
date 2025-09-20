from __future__ import annotations

import warnings
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
    inline_id: str | None = None  # inline_message_id, если есть
    automated: bool = True
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aux_ids(self) -> list[int]:
        warnings.warn("Msg.aux_ids is deprecated; use Msg.extras", DeprecationWarning, stacklevel=2)
        return self.extras

    @aux_ids.setter
    def aux_ids(self, value: list[int]) -> None:
        warnings.warn("Msg.aux_ids is deprecated; use Msg.extras", DeprecationWarning, stacklevel=2)
        self.extras = value

    @property
    def by_bot(self) -> bool:
        warnings.warn("Msg.by_bot is deprecated; use Msg.automated", DeprecationWarning, stacklevel=2)
        return self.automated

    @by_bot.setter
    def by_bot(self, value: bool) -> None:
        warnings.warn("Msg.by_bot is deprecated; use Msg.automated", DeprecationWarning, stacklevel=2)
        self.automated = value


@dataclass(frozen=True, slots=True)
class Entry:
    state: str | None
    view: str | None
    messages: list[Msg]
    root: bool = False

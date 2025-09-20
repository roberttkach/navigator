from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from .markup import Markup
from .media import MediaItem

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Msg:
    id: int
    text: Optional[str]
    media: Optional[MediaItem]  # В истории path = Telegram file_id
    group: Optional[List[MediaItem]]  # В истории path = Telegram file_id
    markup: Optional[Markup]
    preview: Optional["Preview"] = None
    extra: Optional[Dict[str, Any]] = None
    aux_ids: List[int] = field(default_factory=list)
    inline_id: Optional[str] = None  # inline_message_id, если есть
    by_bot: bool = True
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Entry:
    state: Optional[str]
    view: Optional[str]
    messages: List[Msg]
    root: bool = False

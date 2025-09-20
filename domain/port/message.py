from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Optional, Literal, runtime_checkable

from ..value.content import Payload
from ..value.message import Scope


@dataclass(frozen=True, slots=True)
class Result:
    id: int
    extra: List[int]
    # meta:
    kind: Literal["text", "media", "group"]
    media_type: Optional[str] = None
    file_id: Optional[str] = None
    caption: Optional[str] = None
    text: Optional[str] = None
    group_items: Optional[List[dict]] = None  # [{"media_type":..., "file_id":..., "caption": str|None}]
    inline_id: Optional[str] = None


@runtime_checkable
class MessageGateway(Protocol):
    async def send(self, scope: Scope, payload: Payload) -> Result:
        ...

    async def edit_text(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        ...

    async def edit_media(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        ...

    async def edit_caption(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        ...

    async def edit_markup(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        ...

    async def delete(self, scope: Scope, ids: List[int]) -> None:
        ...

    async def notify_empty(self, scope: Scope) -> None:
        ...


__all__ = ["Result", "MessageGateway"]

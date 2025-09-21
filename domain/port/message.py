from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Optional, Literal, runtime_checkable

from ..value.content import Payload
from ..value.message import Scope


@dataclass(frozen=True, slots=True)
class Result:
    id: int
    extra: List[int]
    kind: Literal["text", "media", "group"]
    medium: Optional[str] = None
    file: Optional[str] = None
    caption: Optional[str] = None
    text: Optional[str] = None
    clusters: Optional[List[dict]] = None
    inline: Optional[str] = None


@runtime_checkable
class MessageGateway(Protocol):
    async def send(self, scope: Scope, payload: Payload) -> Result:
        ...

    async def rewrite(self, scope: Scope, message: int, payload: Payload) -> Result:
        ...

    async def recast(self, scope: Scope, message: int, payload: Payload) -> Result:
        ...

    async def retitle(self, scope: Scope, message: int, payload: Payload) -> Result:
        ...

    async def remap(self, scope: Scope, message: int, payload: Payload) -> Result:
        ...

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        ...

    async def alert(self, scope: Scope) -> None:
        ...


__all__ = ["Result", "MessageGateway"]

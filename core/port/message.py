from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import List, Protocol

from ..typing.result import Meta
from ..value.content import Payload
from ..value.message import Scope


@dataclass(frozen=True, slots=True)
class Result:
    id: int
    extra: List[int]
    meta: Meta


@typing.runtime_checkable
class MessageGateway(Protocol):
    async def send(self, scope: Scope, payload: Payload) -> Result:
        ...

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        ...

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        ...

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        ...

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        ...

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        ...

    async def alert(self, scope: Scope, text: str) -> None:
        ...


__all__ = ["Result", "MessageGateway"]

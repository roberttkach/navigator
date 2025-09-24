from __future__ import annotations

import typing
from typing import Protocol

from domain.value.message import Scope


@typing.runtime_checkable
class ExtraSchema(Protocol):
    def for_send(
        self,
        scope: Scope,
        extra: dict | None,
        *,
        caption_len: int,
        media: bool,
    ) -> dict:
        ...

    def for_edit(
        self,
        scope: Scope,
        extra: dict | None,
        *,
        caption_len: int,
        media: bool,
    ) -> dict:
        ...

    def for_history(self, extra: dict | None, *, length: int) -> dict | None:
        ...


__all__ = ["ExtraSchema"]

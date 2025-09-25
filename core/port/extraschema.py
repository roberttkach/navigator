from __future__ import annotations

import typing
from typing import Protocol

from ..value.message import Scope


@typing.runtime_checkable
class ExtraSchema(Protocol):
    def send(
            self,
            scope: Scope,
            extra: dict | None,
            *,
            span: int,
            media: bool,
    ) -> dict:
        ...

    def edit(
            self,
            scope: Scope,
            extra: dict | None,
            *,
            span: int,
            media: bool,
    ) -> dict:
        ...

    def history(self, extra: dict | None, *, length: int) -> dict | None:
        ...


__all__ = ["ExtraSchema"]

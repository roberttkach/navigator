from __future__ import annotations

from typing import Any, TYPE_CHECKING

from navigator.api import build_navigator
from navigator.core.port.factory import ViewLedger

from .scope import outline

if TYPE_CHECKING:  # pragma: no cover - typing only
    from navigator.presentation.navigator import Navigator


async def assemble(event: Any, state: Any, ledger: ViewLedger) -> "Navigator":
    scope = outline(event)
    return await build_navigator(event=event, state=state, ledger=ledger, scope=scope)


__all__ = ["assemble"]

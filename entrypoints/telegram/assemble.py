from __future__ import annotations

from navigator.api import assemble as invoke
from navigator.core.port.factory import ViewLedger
from typing import Any, TYPE_CHECKING

from .scope import outline

if TYPE_CHECKING:  # pragma: no cover - typing only
    from navigator.presentation.navigator import Navigator


async def assemble(event: Any, state: Any, ledger: ViewLedger) -> "Navigator":
    scope = outline(event)
    return await invoke(event=event, state=state, ledger=ledger, scope=scope)


__all__ = ["assemble"]

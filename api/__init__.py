"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..core.port.factory import ViewLedger
from ..infra.di.bootstrap import build_navigator as _bootstrap
from ..core.value.message import Scope

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..presentation.navigator import Navigator


async def build_navigator(event: Any, state: Any, ledger: ViewLedger, scope: Scope) -> "Navigator":
    """Assemble a Navigator facade using the infrastructure bootstrap."""

    return await _bootstrap(event=event, state=state, ledger=ledger, scope=scope)


__all__ = ["build_navigator"]

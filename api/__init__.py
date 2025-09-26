"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, Iterable, cast

from .contracts import NavigatorLike, ScopeDTO, ViewLedgerDTO
from ..app.service.navigator_runtime import MissingAlert
from ..bootstrap.navigator import NavigatorAssembler, assemble as _bootstrap


async def assemble(
        event: Any,
        state: Any,
        ledger: ViewLedgerDTO,
        scope: ScopeDTO,
        instrumentation: Iterable[NavigatorAssembler.Instrument] | None = None,
        *,
        missing_alert: MissingAlert | None = None,
) -> NavigatorLike:
    """Assemble and return a Navigator facade instance."""

    navigator = await _bootstrap(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=instrumentation,
        missing_alert=missing_alert,
    )
    return cast(NavigatorLike, navigator)


__all__ = ["assemble"]

"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, Iterable, cast

from .contracts import NavigatorLike, ScopeDTO, ViewLedgerDTO
from ..app.service.navigator_runtime import MissingAlert
from ..bootstrap.navigator import NavigatorAssembler, assemble as _bootstrap
from ..presentation.bootstrap.navigator import wrap_runtime


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

    bundle = await _bootstrap(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=instrumentation,
        missing_alert=missing_alert,
    )
    navigator = wrap_runtime(bundle.runtime)
    return cast(NavigatorLike, navigator)


__all__ = ["assemble"]

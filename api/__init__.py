"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, Iterable, cast

from .contracts import (
    NavigatorLike,
    NavigatorRuntimeInstrument,
    ScopeDTO,
    ViewLedgerDTO,
)
from ..app.service.navigator_runtime import MissingAlert
from ..app.service.navigator_runtime.facade import NavigatorFacade
from ..bootstrap.navigator import assemble as _bootstrap
from ..bootstrap.navigator.context import ViewContainerFactory


async def assemble(
        event: Any,
        state: Any,
        ledger: ViewLedgerDTO,
        scope: ScopeDTO,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        *,
        missing_alert: MissingAlert | None = None,
        view_container: ViewContainerFactory | None = None,
) -> NavigatorLike:
    """Assemble and return a Navigator facade instance."""

    bootstrap_kwargs = {
        "missing_alert": missing_alert,
    }
    if view_container is not None:
        bootstrap_kwargs["view_container"] = view_container
    bundle = await _bootstrap(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=instrumentation,
        **bootstrap_kwargs,
    )
    navigator = NavigatorFacade(bundle.runtime)
    return cast(NavigatorLike, navigator)


__all__ = ["assemble"]

"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, Iterable, cast

from navigator.adapters.navigator_runtime import bootstrap_runtime_assembler_resolver
from navigator.app.service.navigator_runtime.entrypoints import assemble_navigator
from ._scope import scope_from_dto
from .contracts import (
    NavigatorAssemblyOverrides,
    NavigatorLike,
    NavigatorRuntimeInstrument,
    ScopeDTO,
    ViewLedgerDTO,
)
from ..core.contracts import MissingAlert


async def assemble(
        event: Any,
        state: Any,
        ledger: ViewLedgerDTO,
        scope: ScopeDTO,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        *,
        missing_alert: MissingAlert | None = None,
        overrides: NavigatorAssemblyOverrides | None = None,
) -> NavigatorLike:
    """Assemble and return a Navigator facade instance."""

    navigator = await assemble_navigator(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope_from_dto(scope),
        instrumentation=instrumentation,
        missing_alert=missing_alert,
        overrides=overrides,
        assembler_resolver=bootstrap_runtime_assembler_resolver(),
    )
    return cast(NavigatorLike, navigator)


__all__ = ["assemble"]

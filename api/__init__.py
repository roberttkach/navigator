"""Public entry points for embedding Navigator."""
from __future__ import annotations

from typing import Any, cast

from .contracts import NavigatorLike, ScopeDTO, ViewLedgerDTO
from ..bootstrap.navigator import build_navigator as _bootstrap


async def build_navigator(
    event: Any,
    state: Any,
    ledger: ViewLedgerDTO,
    scope: ScopeDTO,
) -> NavigatorLike:
    """Assemble and return a Navigator facade instance."""

    navigator = await _bootstrap(event=event, state=state, ledger=ledger, scope=scope)
    return cast(NavigatorLike, navigator)


__all__ = ["build_navigator"]

from __future__ import annotations

from navigator.api import assemble as invoke
from navigator.core.port.factory import ViewLedger
from typing import Any, TYPE_CHECKING

from .scope import outline
from navigator.presentation.alerts import missing
from navigator.presentation.telegram import router
from navigator.presentation.telegram.instrumentation import build_retreat_instrument
from navigator.presentation.telegram.router import retreat_configurator

if TYPE_CHECKING:  # pragma: no cover - typing only
    from navigator.presentation.navigator import Navigator


async def assemble(event: Any, state: Any, ledger: ViewLedger) -> "Navigator":
    scope = outline(event)
    instrument = build_retreat_instrument(retreat_configurator(router))
    return await invoke(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=(instrument,),
        missing_alert=missing,
    )


__all__ = ["assemble"]

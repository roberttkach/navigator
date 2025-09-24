from __future__ import annotations

from typing import Any, cast

from navigator.adapters.telemetry.logger import PythonLoggingTelemetry
from navigator.api.contracts import ScopeDTO, ViewLedgerDTO
from navigator.core.port.factory import ViewForge, ViewLedger
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.infra.di.container import AppContainer
from navigator.presentation.alerts import missing
from navigator.presentation.telegram import instrument
from navigator.presentation.bootstrap.navigator import compose
from navigator.presentation.navigator import Navigator


class _LedgerAdapter(ViewLedger):
    def __init__(self, ledger: ViewLedgerDTO) -> None:
        self._ledger = ledger

    def get(self, key: str) -> ViewForge:
        forge = self._ledger.get(key)
        if not callable(forge):
            raise TypeError(f"Ledger forge for '{key}' is not callable")
        return cast(ViewForge, forge)

    def has(self, key: str) -> bool:
        return bool(self._ledger.has(key))


def _convert_scope(dto: ScopeDTO) -> Scope:
    return Scope(
        chat=getattr(dto, "chat", None),
        lang=getattr(dto, "lang", None),
        inline=getattr(dto, "inline", None),
        business=getattr(dto, "business", None),
        category=getattr(dto, "category", None),
        topic=getattr(dto, "topic", None),
    )


async def assemble(
    *,
    event: Any,
    state: Any,
    ledger: ViewLedgerDTO,
    scope: ScopeDTO,
) -> Navigator:
    telemetry_port = PythonLoggingTelemetry()
    telemetry = Telemetry(telemetry_port)
    container = AppContainer(
        event=event,
        state=state,
        ledger=_LedgerAdapter(ledger),
        alert=missing,
        telemetry=telemetry,
    )
    settings = container.core().settings()
    mode = getattr(settings, "redaction", "")
    telemetry.calibrate(mode)
    instrument(telemetry)
    return compose(container, _convert_scope(scope))


__all__ = ["assemble"]

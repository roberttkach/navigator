"""Bootstrap the Navigator runtime for telegram entrypoints."""

from __future__ import annotations

from typing import Any, cast

from navigator.adapters.telemetry.logger import PythonLoggingTelemetry
from navigator.api.contracts import ScopeDTO, ViewLedgerDTO
from navigator.core.port.factory import ViewForge, ViewLedger
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.infra.di.container import AppContainer
from navigator.presentation.alerts import missing
from navigator.presentation.bootstrap.navigator import compose
from navigator.presentation.navigator import Navigator
from navigator.presentation.telegram import instrument


class _LedgerAdapter(ViewLedger):
    """Expose a DTO-backed ledger through the domain ``ViewLedger``."""

    def __init__(self, ledger: ViewLedgerDTO) -> None:
        self._ledger = ledger

    def get(self, key: str) -> ViewForge:
        """Return a forge callable for ``key`` ensuring callability."""

        forge = self._ledger.get(key)
        if not callable(forge):
            raise TypeError(f"Ledger forge for '{key}' is not callable")
        return cast(ViewForge, forge)

    def has(self, key: str) -> bool:
        """Return ``True`` when the underlying ledger exposes ``key``."""

        return bool(self._ledger.has(key))


def _scope(dto: ScopeDTO) -> Scope:
    """Translate external ``ScopeDTO`` structures into domain scopes."""

    return Scope(
        chat=getattr(dto, "chat", None),
        lang=getattr(dto, "lang", None),
        inline=getattr(dto, "inline", None),
        business=getattr(dto, "business", None),
        category=getattr(dto, "category", None),
        topic=getattr(dto, "topic", None),
        direct=bool(getattr(dto, "direct", False)),
    )


async def assemble(
        *,
        event: Any,
        state: Any,
        ledger: ViewLedgerDTO,
        scope: ScopeDTO,
) -> Navigator:
    """Construct a Navigator instance from entrypoint payloads."""

    port = PythonLoggingTelemetry()
    telemetry = Telemetry(port)
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
    return compose(container, _scope(scope))


__all__ = ["assemble"]

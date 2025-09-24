from __future__ import annotations

from typing import Any

from navigator.adapters.telemetry.python_logging import PythonLoggingTelemetry
from navigator.core.port.factory import ViewLedger
from navigator.core.telemetry import telemetry
from navigator.core.value.message import Scope
from navigator.infra.di.container import AppContainer
from navigator.presentation.alerts import prev_not_found
from navigator.presentation.bootstrap.navigator import build_navigator as assemble
from navigator.presentation.navigator import Navigator


def _ensure_telemetry(mode: str) -> None:
    if not telemetry.bound():
        telemetry.bind(PythonLoggingTelemetry())
    telemetry.calibrate(mode)


async def build_navigator(
    *,
    event: Any,
    state: Any,
    ledger: ViewLedger,
    scope: Scope,
) -> Navigator:
    container = AppContainer(event=event, state=state, ledger=ledger, alert=prev_not_found)
    settings = container.core().settings()
    mode = getattr(settings, "redaction", "")
    _ensure_telemetry(mode)
    return assemble(container, scope)


__all__ = ["build_navigator"]

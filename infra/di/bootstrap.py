"""Composition root for building the Navigator facade."""
from __future__ import annotations

from typing import Any

from navigator.core.port.factory import ViewLedger
from navigator.core.telemetry import telemetry
from navigator.core.value.message import Scope
from navigator.presentation.alerts import prev_not_found
from navigator.presentation.bootstrap.navigator import build_navigator as assemble
from navigator.presentation.navigator import Navigator

from .container import AppContainer
from ...adapters.telemetry.python_logging import PythonLoggingTelemetry


def _ensure_telemetry(mode: str) -> None:
    """Bind and configure telemetry for the current process."""

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
    """Create a Navigator facade wired with infrastructure dependencies."""

    container = AppContainer(event=event, state=state, ledger=ledger, alert=prev_not_found)
    settings = container.core().settings()
    mode = getattr(settings, "redaction", "")
    _ensure_telemetry(mode)
    return assemble(container, scope)


__all__ = ["build_navigator"]

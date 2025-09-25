"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer
from navigator.presentation.alerts import missing

from .adapter import LedgerAdapter
from .context import BootstrapContext


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._telemetry = telemetry

    def create(self, context: BootstrapContext) -> AppContainer:
        return AppContainer(
            event=context.event,
            state=context.state,
            ledger=LedgerAdapter(context.ledger),
            alert=missing,
            telemetry=self._telemetry,
        )


__all__ = ["ContainerFactory"]

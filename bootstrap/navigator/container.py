"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer

from .adapter import LedgerAdapter
from .context import BootstrapContext


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(
        self,
        telemetry: Telemetry,
        *,
        alert: MissingAlert | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._alert = alert or (lambda scope: "")

    def create(self, context: BootstrapContext) -> AppContainer:
        alert = context.missing_alert or self._alert
        return AppContainer(
            event=context.event,
            state=context.state,
            ledger=LedgerAdapter(context.ledger),
            alert=alert,
            telemetry=self._telemetry,
        )


__all__ = ["ContainerFactory"]

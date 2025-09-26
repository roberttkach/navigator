"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.telemetry import Telemetry
from typing import TYPE_CHECKING

from .adapter import LedgerAdapter
from .context import BootstrapContext, ViewContainerFactory

if TYPE_CHECKING:
    from navigator.infra.di.container import AppContainer


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(
        self,
        telemetry: Telemetry,
        *,
        alert: MissingAlert | None = None,
        view_container: ViewContainerFactory | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._alert = alert or (lambda scope: "")
        self._view_container = view_container

    def create(self, context: BootstrapContext) -> "AppContainer":
        alert = context.missing_alert or self._alert
        view_container = context.view_container or self._view_container
        if view_container is None:
            raise ValueError("view_container must be provided to ContainerFactory")
        from navigator.infra.di.container import AppContainer  # local import

        return AppContainer(
            event=context.event,
            state=context.state,
            ledger=LedgerAdapter(context.ledger),
            alert=alert,
            telemetry=self._telemetry,
            view_container=view_container,
        )


__all__ = ["ContainerFactory"]

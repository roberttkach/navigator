"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.core.contracts import MissingAlert
from navigator.core.telemetry import Telemetry

from .adapter import LedgerAdapter
from .container_resolution import resolve_container_builder, resolve_view_container
from .container_types import ContainerBuilder, ContainerRequest, RuntimeContainer
from .context import BootstrapContext, ViewContainerFactory


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(
        self,
        telemetry: Telemetry,
        *,
        alert: MissingAlert | None = None,
        view_container: ViewContainerFactory | None = None,
        builder: ContainerBuilder | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._alert = alert or (lambda scope: "")
        self._view_container = view_container
        self._builder = builder

    def create(self, context: BootstrapContext) -> RuntimeContainer:
        alert = context.missing_alert or self._alert
        view_container = context.view_container or self._view_container
        if view_container is None:
            view_container = resolve_view_container()
        builder = self._builder or resolve_container_builder()
        request = ContainerRequest(
            event=context.event,
            state=context.state,
            ledger=LedgerAdapter(context.ledger),
            alert=alert,
            telemetry=self._telemetry,
            view_container=view_container,
        )
        return builder.build(request)


__all__ = ["ContainerFactory"]

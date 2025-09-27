"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.core.contracts import MissingAlert
from navigator.core.telemetry import Telemetry

from .adapter import LedgerAdapter
from .container_collaborators import ContainerCollaboratorsResolver
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
        self._collaborators = ContainerCollaboratorsResolver(
            default_view=view_container,
            default_builder=builder,
        )

    def create(self, context: BootstrapContext) -> RuntimeContainer:
        alert = context.missing_alert or self._alert
        collaborators = self._collaborators.resolve(context)
        request = ContainerRequest(
            event=context.event,
            state=context.state,
            ledger=LedgerAdapter(context.ledger),
            alert=alert,
            telemetry=self._telemetry,
            view_container=collaborators.view_container,
        )
        return collaborators.builder.build(request)


__all__ = ["ContainerFactory"]

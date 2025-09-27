"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from navigator.core.contracts import MissingAlert
from navigator.core.telemetry import Telemetry

from .adapter import LedgerAdapter
from .container_collaborators import ContainerCollaboratorsResolver
from .container_resolution import ContainerResolution, create_container_resolution
from .container_types import ContainerBuilder, ContainerRequest, RuntimeContainer
from .context import BootstrapContext, ViewContainerFactory


class ContainerRequestFactory:
    """Create container requests from bootstrap context information."""

    def __init__(self, *, telemetry: Telemetry, alert: MissingAlert) -> None:
        self._telemetry = telemetry
        self._default_alert = alert

    def create(
        self,
        context: BootstrapContext,
        *,
        view_container: ViewContainerFactory,
    ) -> ContainerRequest:
        """Build a container request isolating ledger adaptation and alerts."""

        return ContainerRequest(
            event=context.event,
            state=context.state,
            ledger=self._adapt_ledger(context),
            alert=self._select_alert(context),
            telemetry=self._telemetry,
            view_container=view_container,
        )

    def _select_alert(self, context: BootstrapContext) -> MissingAlert:
        return context.missing_alert or self._default_alert

    @staticmethod
    def _adapt_ledger(context: BootstrapContext) -> LedgerAdapter:
        return LedgerAdapter(context.ledger)


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(
        self,
        *,
        telemetry: Telemetry,
        alert: MissingAlert | None = None,
        view_container: ViewContainerFactory | None = None,
        builder: ContainerBuilder | None = None,
        resolution: ContainerResolution | None = None,
        request_factory: ContainerRequestFactory | None = None,
    ) -> None:
        default_alert = alert or (lambda scope: "")
        self._request_factory = request_factory or ContainerRequestFactory(
            telemetry=telemetry,
            alert=default_alert,
        )
        self._collaborators = ContainerCollaboratorsResolver(
            default_view=view_container,
            default_builder=builder,
            resolution=resolution or create_container_resolution(),
        )

    def create(self, context: BootstrapContext) -> RuntimeContainer:
        collaborators = self._collaborators.resolve(context)
        request = self._request_factory.create(
            context,
            view_container=collaborators.view_container,
        )
        return collaborators.builder.build(request)


__all__ = ["ContainerFactory", "ContainerRequestFactory"]

"""Factories assembling the dependency injection container for the runtime."""
from __future__ import annotations

from dataclasses import dataclass

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
        collaborators: ContainerCollaboratorsResolver,
        request_factory: ContainerRequestFactory,
    ) -> None:
        self._collaborators = collaborators
        self._request_factory = request_factory

    def create(self, context: BootstrapContext) -> RuntimeContainer:
        collaborators = self._collaborators.resolve(context)
        request = self._request_factory.create(
            context,
            view_container=collaborators.view_container,
        )
        return collaborators.builder.build(request)


@dataclass(slots=True)
class RequestFactorySelector:
    """Pick the container request factory according to builder inputs."""

    telemetry: Telemetry
    alert: MissingAlert | None
    candidate: ContainerRequestFactory | None = None

    def select(self) -> ContainerRequestFactory:
        if self.candidate is not None:
            return self.candidate
        default_alert = self.alert or (lambda scope: "")
        return ContainerRequestFactory(telemetry=self.telemetry, alert=default_alert)


@dataclass(slots=True)
class CollaboratorResolverSelector:
    """Pick the collaborator resolver while isolating default construction."""

    view_container: ViewContainerFactory | None
    builder: ContainerBuilder | None
    resolution: ContainerResolution | None
    candidate: ContainerCollaboratorsResolver | None = None

    def select(self) -> ContainerCollaboratorsResolver:
        if self.candidate is not None:
            return self.candidate
        resolved = self.resolution or create_container_resolution()
        return ContainerCollaboratorsResolver(
            default_view=self.view_container,
            default_builder=self.builder,
            resolution=resolved,
        )


@dataclass(slots=True)
class ContainerFactoryContext:
    """Store immutable factory configuration for cohesive selection logic."""

    telemetry: Telemetry
    alert: MissingAlert | None = None
    view_container: ViewContainerFactory | None = None
    builder: ContainerBuilder | None = None
    resolution: ContainerResolution | None = None


class ContainerFactoryBuilder:
    """Wire container factory collaborators behind dedicated selectors."""

    def __init__(
        self,
        context: ContainerFactoryContext,
        *,
        request_factory: ContainerRequestFactory | None = None,
        collaborators: ContainerCollaboratorsResolver | None = None,
    ) -> None:
        self._context = context
        self._request_factory = request_factory
        self._collaborators = collaborators

    def build(self) -> ContainerFactory:
        blueprint = self._create_blueprint()
        return blueprint.assemble()

    def _create_blueprint(self) -> "ContainerFactoryBlueprint":
        return ContainerFactoryBlueprint(
            request_factory=self._select_request_factory(),
            collaborators=self._select_collaborators(),
        )

    def _select_request_factory(self) -> ContainerRequestFactory:
        selector = RequestFactorySelector(
            telemetry=self._context.telemetry,
            alert=self._context.alert,
            candidate=self._request_factory,
        )
        return selector.select()

    def _select_collaborators(self) -> ContainerCollaboratorsResolver:
        selector = CollaboratorResolverSelector(
            view_container=self._context.view_container,
            builder=self._context.builder,
            resolution=self._context.resolution,
            candidate=self._collaborators,
        )
        return selector.select()


@dataclass(slots=True)
class ContainerFactoryBlueprint:
    """Capture selected collaborators before building the factory."""

    request_factory: ContainerRequestFactory
    collaborators: ContainerCollaboratorsResolver

    def assemble(self) -> ContainerFactory:
        return ContainerFactory(
            collaborators=self.collaborators,
            request_factory=self.request_factory,
        )


__all__ = [
    "ContainerFactory",
    "ContainerFactoryContext",
    "ContainerFactoryBuilder",
    "ContainerRequestFactory",
]

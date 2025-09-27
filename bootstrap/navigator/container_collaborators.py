"""Utilities resolving collaborators required to build runtime containers."""
from __future__ import annotations

from dataclasses import dataclass

from .container_resolution import ContainerResolution, create_container_resolution
from .container_types import ContainerBuilder, ViewContainerFactory
from .context import BootstrapContext


@dataclass(frozen=True)
class ContainerCollaborators:
    """Bundle of infrastructure collaborators used by the container factory."""

    builder: ContainerBuilder
    view_container: ViewContainerFactory


class ContainerCollaboratorsResolver:
    """Resolve container collaborators while honouring bootstrap overrides."""

    def __init__(
        self,
        *,
        default_view: ViewContainerFactory | None = None,
        default_builder: ContainerBuilder | None = None,
        resolution: ContainerResolution | None = None,
    ) -> None:
        self._default_view = default_view
        self._default_builder = default_builder
        self._resolution = resolution or create_container_resolution()

    def resolve(self, context: BootstrapContext) -> ContainerCollaborators:
        view_container = context.view_container or self._default_view
        if view_container is None:
            view_container = self._resolution.resolve_view_container()
        builder = self._default_builder or self._resolution.resolve_container_builder()
        return ContainerCollaborators(builder=builder, view_container=view_container)


__all__ = [
    "ContainerCollaborators",
    "ContainerCollaboratorsResolver",
]

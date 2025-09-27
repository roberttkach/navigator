"""Helpers resolving runtime factories and view containers."""
from __future__ import annotations

from dataclasses import dataclass

from .container_resolution import ContainerResolution, create_container_resolution
from .context import ViewContainerFactory
from .runtime import ContainerRuntimeFactory, NavigatorFactory


@dataclass(slots=True)
class ViewContainerResolver:
    """Resolve the view container using configured resolution policy."""

    resolution: ContainerResolution

    def resolve(self, candidate: ViewContainerFactory | None) -> ViewContainerFactory:
        if candidate is not None:
            return candidate
        return self.resolution.resolve_view_container()


@dataclass(slots=True)
class RuntimeFactoryResolver:
    """Resolve runtime factories from bootstrap collaborators."""

    view_resolver: ViewContainerResolver
    default_view: ViewContainerFactory | None = None

    def resolve(
        self,
        *,
        runtime_factory: NavigatorFactory | None,
        context_view: ViewContainerFactory | None,
    ) -> NavigatorFactory:
        if runtime_factory is not None:
            return runtime_factory
        candidate = context_view or self.default_view
        container = self.view_resolver.resolve(candidate)
        return ContainerRuntimeFactory(view_container=container)


def create_runtime_factory_resolver(
    *,
    resolution: ContainerResolution | None = None,
    default_view: ViewContainerFactory | None = None,
    resolver: RuntimeFactoryResolver | None = None,
) -> RuntimeFactoryResolver:
    """Create a resolver pre-configured with container resolution policies."""

    if resolver is not None:
        return resolver
    resolved_resolution = resolution or create_container_resolution()
    view_resolver = ViewContainerResolver(resolved_resolution)
    return RuntimeFactoryResolver(view_resolver, default_view=default_view)


__all__ = [
    "RuntimeFactoryResolver",
    "ViewContainerResolver",
    "create_runtime_factory_resolver",
]

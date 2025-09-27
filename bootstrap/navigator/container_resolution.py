"""Resolution helpers for container-related collaborators."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol, TypeVar, cast

from .container_errors import ContainerResolutionError
from .container_types import ContainerBuilder, ViewContainerFactory
from .default_container_loader import default_builder_loader, default_view_loader


T_co = TypeVar("T_co")


class _Loader(Protocol[T_co]):
    def __call__(self) -> T_co: ...


@dataclass(frozen=True)
class _ResolutionDefaults:
    view: _Loader[ViewContainerFactory]
    builder: _Loader[ContainerBuilder]


@dataclass(frozen=True)
class _ResolutionOverrides:
    view: _Loader[ViewContainerFactory] | None = None
    builder: _Loader[ContainerBuilder] | None = None


class ContainerResolutionRegistry:
    """Manage overrides for container collaborator resolution."""

    def __init__(self, defaults: _ResolutionDefaults) -> None:
        self._defaults = defaults
        self._overrides = _ResolutionOverrides()

    def configure_view(
        self, candidate: _Loader[ViewContainerFactory] | ViewContainerFactory
    ) -> None:
        self._overrides = replace(
            self._overrides, view=_ensure_view_loader(candidate)
        )

    def configure_builder(
        self, candidate: _Loader[ContainerBuilder] | ContainerBuilder
    ) -> None:
        self._overrides = replace(
            self._overrides, builder=_ensure_builder_loader(candidate)
        )

    def view_factory(self) -> ViewContainerFactory:
        loader = self._overrides.view or self._defaults.view
        return loader()

    def container_builder(self) -> ContainerBuilder:
        loader = self._overrides.builder or self._defaults.builder
        builder = loader()
        if not hasattr(builder, "build"):
            raise ContainerResolutionError(
                "Resolved container builder does not expose a 'build' method"
            )
        return builder


_defaults = _ResolutionDefaults(
    view=default_view_loader,
    builder=default_builder_loader,
)
_registry = ContainerResolutionRegistry(_defaults)


def configure_view_container(
    factory: _Loader[ViewContainerFactory] | ViewContainerFactory,
) -> None:
    """Override the default view container factory resolution."""

    _registry.configure_view(factory)


def configure_container_builder(
    builder: _Loader[ContainerBuilder] | ContainerBuilder,
) -> None:
    """Override the default container builder resolution."""

    _registry.configure_builder(builder)


def resolve_view_container() -> ViewContainerFactory:
    """Return the default view container factory."""

    try:
        return _registry.view_factory()
    except (ImportError, AttributeError) as exc:
        raise ContainerResolutionError("Unable to resolve default view container") from exc


def resolve_container_builder() -> ContainerBuilder:
    """Return the default runtime container builder."""

    try:
        return _registry.container_builder()
    except (ImportError, AttributeError, TypeError) as exc:
        raise ContainerResolutionError("Unable to resolve container builder") from exc


def _ensure_view_loader(
    loader: _Loader[ViewContainerFactory] | ViewContainerFactory,
) -> _Loader[ViewContainerFactory]:
    if callable(loader) and not isinstance(loader, type):
        return cast(_Loader[ViewContainerFactory], loader)

    def _factory() -> ViewContainerFactory:
        if isinstance(loader, type):
            return loader
        return cast(ViewContainerFactory, loader)

    return _factory


def _ensure_builder_loader(
    loader: _Loader[ContainerBuilder] | ContainerBuilder,
) -> _Loader[ContainerBuilder]:
    if callable(getattr(loader, "build", None)) and not isinstance(loader, type):
        return lambda: cast(ContainerBuilder, loader)
    if callable(loader) and not isinstance(loader, type):
        return cast(_Loader[ContainerBuilder], loader)

    def _factory() -> ContainerBuilder:
        if isinstance(loader, type):
            instance = loader()  # type: ignore[call-arg]
        else:
            instance = cast(ContainerBuilder, loader)
        if not hasattr(instance, "build"):
            raise ContainerResolutionError(
                "Configured builder does not provide a 'build' method"
            )
        return cast(ContainerBuilder, instance)

    return _factory


__all__ = [
    "ContainerResolutionRegistry",
    "configure_container_builder",
    "configure_view_container",
    "resolve_container_builder",
    "resolve_view_container",
]

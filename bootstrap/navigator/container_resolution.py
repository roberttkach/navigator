"""Default resolution helpers for container-related collaborators."""
from __future__ import annotations

import os
from importlib import import_module
from dataclasses import dataclass, replace
from typing import Protocol, TypeVar, cast

from .container_types import ContainerBuilder, ViewContainerFactory


DEFAULT_VIEW_CONTAINER_PATH = "navigator.infra.di.container.telegram:TelegramContainer"
DEFAULT_CONTAINER_BUILDER_PATH = "navigator.infra.di.container.builder:NavigatorContainerBuilder"
ENV_VIEW_CONTAINER = "NAVIGATOR_VIEW_CONTAINER"
ENV_CONTAINER_BUILDER = "NAVIGATOR_CONTAINER_BUILDER"


T_co = TypeVar("T_co")


class _Loader(Protocol[T_co]):
    def __call__(self) -> T_co: ...


class ContainerResolutionError(LookupError):
    """Raised when default container collaborators cannot be resolved."""


@dataclass(frozen=True)
class ContainerResolver:
    """Resolve container collaborators without depending on global caches."""

    view_loader: _Loader[ViewContainerFactory] | None = None
    builder_loader: _Loader[ContainerBuilder] | None = None

    def with_view(
        self, candidate: _Loader[ViewContainerFactory] | ViewContainerFactory
    ) -> "ContainerResolver":
        return replace(self, view_loader=_ensure_view_loader(candidate))

    def with_builder(
        self, candidate: _Loader[ContainerBuilder] | ContainerBuilder
    ) -> "ContainerResolver":
        return replace(self, builder_loader=_ensure_builder_loader(candidate))

    def view_factory(self) -> ViewContainerFactory:
        loader = self.view_loader or _default_view_loader
        return loader()

    def container_builder(self) -> ContainerBuilder:
        loader = self.builder_loader or _default_builder_loader
        builder = loader()
        if not hasattr(builder, "build"):
            raise ContainerResolutionError(
                "Resolved container builder does not expose a 'build' method"
            )
        return builder


_resolver = ContainerResolver()


def configure_view_container(
    factory: _Loader[ViewContainerFactory] | ViewContainerFactory,
) -> None:
    """Override the default view container factory resolution."""

    global _resolver
    _resolver = _resolver.with_view(factory)


def configure_container_builder(
    builder: _Loader[ContainerBuilder] | ContainerBuilder,
) -> None:
    """Override the default container builder resolution."""

    global _resolver
    _resolver = _resolver.with_builder(builder)


def resolve_view_container() -> ViewContainerFactory:
    """Return the default view container factory."""

    try:
        return _resolver.view_factory()
    except (ImportError, AttributeError) as exc:
        raise ContainerResolutionError("Unable to resolve default view container") from exc


def resolve_container_builder() -> ContainerBuilder:
    """Return the default runtime container builder."""

    try:
        return _resolver.container_builder()
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


def _default_view_loader() -> ViewContainerFactory:
    path = os.getenv(ENV_VIEW_CONTAINER, DEFAULT_VIEW_CONTAINER_PATH)
    container = _import_symbol(path)
    if not isinstance(container, type):
        raise ContainerResolutionError(
            f"Default view container '{path}' is not a container class"
        )
    return cast(ViewContainerFactory, container)


def _default_builder_loader() -> ContainerBuilder:
    path = os.getenv(ENV_CONTAINER_BUILDER, DEFAULT_CONTAINER_BUILDER_PATH)
    symbol = _import_symbol(path)
    if isinstance(symbol, type):
        instance = symbol()  # type: ignore[call-arg]
    else:
        instance = symbol
    if not hasattr(instance, "build"):
        raise ContainerResolutionError(
            f"Default builder '{path}' does not implement a 'build' method"
        )
    return cast(ContainerBuilder, instance)


def _import_symbol(path: str):
    module_path, _, attribute = path.partition(":")
    if not module_path or not attribute:
        raise ContainerResolutionError(
            f"Invalid module path '{path}' provided for container resolution"
        )
    module = import_module(module_path)
    try:
        return getattr(module, attribute)
    except AttributeError as exc:
        raise ContainerResolutionError(
            f"Module '{module_path}' does not expose attribute '{attribute}'"
        ) from exc


__all__ = [
    "ContainerResolutionError",
    "configure_container_builder",
    "configure_view_container",
    "resolve_container_builder",
    "resolve_view_container",
]

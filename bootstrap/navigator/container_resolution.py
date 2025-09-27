"""Default resolution helpers for container-related collaborators."""
from __future__ import annotations

import os
from importlib import import_module
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


class _ResolutionState:
    """Track overrides and cached resolution results."""

    def __init__(self) -> None:
        self._view_loader: _Loader[ViewContainerFactory] | None = None
        self._builder_loader: _Loader[ContainerBuilder] | None = None
        self._view_cache: ViewContainerFactory | None = None
        self._builder_cache: ContainerBuilder | None = None

    def configure_view_container(
        self, loader: _Loader[ViewContainerFactory] | ViewContainerFactory
    ) -> None:
        self._view_loader = _ensure_view_loader(loader)
        self._view_cache = None

    def configure_container_builder(
        self, loader: _Loader[ContainerBuilder] | ContainerBuilder
    ) -> None:
        self._builder_loader = _ensure_builder_loader(loader)
        self._builder_cache = None

    def resolve_view_container(self) -> ViewContainerFactory:
        if self._view_cache is not None:
            return self._view_cache
        loader = self._view_loader or _default_view_loader
        container = loader()
        self._view_cache = container
        return container

    def resolve_container_builder(self) -> ContainerBuilder:
        if self._builder_cache is not None:
            return self._builder_cache
        loader = self._builder_loader or _default_builder_loader
        builder = loader()
        if not hasattr(builder, "build"):
            raise ContainerResolutionError(
                "Resolved container builder does not expose a 'build' method"
            )
        self._builder_cache = builder
        return builder


_state = _ResolutionState()


def configure_view_container(
    factory: _Loader[ViewContainerFactory] | ViewContainerFactory,
) -> None:
    """Override the default view container factory resolution."""

    _state.configure_view_container(factory)


def configure_container_builder(
    builder: _Loader[ContainerBuilder] | ContainerBuilder,
) -> None:
    """Override the default container builder resolution."""

    _state.configure_container_builder(builder)


def resolve_view_container() -> ViewContainerFactory:
    """Return the default view container factory."""

    try:
        return _state.resolve_view_container()
    except (ImportError, AttributeError) as exc:
        raise ContainerResolutionError("Unable to resolve default view container") from exc


def resolve_container_builder() -> ContainerBuilder:
    """Return the default runtime container builder."""

    try:
        return _state.resolve_container_builder()
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

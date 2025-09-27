"""Default resolution helpers for container-related collaborators."""
from __future__ import annotations

import os
from importlib import import_module
from dataclasses import dataclass
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


@dataclass
class _ViewFactoryRegistry:
    """Maintain override and cache state for view container factories."""

    loader: _Loader[ViewContainerFactory] | None = None
    cache: ViewContainerFactory | None = None

    def configure(
        self, candidate: _Loader[ViewContainerFactory] | ViewContainerFactory
    ) -> None:
        self.loader = _ensure_view_loader(candidate)
        self.cache = None

    def resolve(self) -> ViewContainerFactory:
        if self.cache is None:
            factory = (self.loader or _default_view_loader)()
            self.cache = factory
        return self.cache


@dataclass
class _BuilderRegistry:
    """Maintain override and cache state for container builders."""

    loader: _Loader[ContainerBuilder] | None = None
    cache: ContainerBuilder | None = None

    def configure(
        self, candidate: _Loader[ContainerBuilder] | ContainerBuilder
    ) -> None:
        self.loader = _ensure_builder_loader(candidate)
        self.cache = None

    def resolve(self) -> ContainerBuilder:
        if self.cache is None:
            builder = (self.loader or _default_builder_loader)()
            if not hasattr(builder, "build"):
                raise ContainerResolutionError(
                    "Resolved container builder does not expose a 'build' method"
                )
            self.cache = builder
        return self.cache


_view_registry = _ViewFactoryRegistry()
_builder_registry = _BuilderRegistry()


def configure_view_container(
    factory: _Loader[ViewContainerFactory] | ViewContainerFactory,
) -> None:
    """Override the default view container factory resolution."""

    _view_registry.configure(factory)


def configure_container_builder(
    builder: _Loader[ContainerBuilder] | ContainerBuilder,
) -> None:
    """Override the default container builder resolution."""

    _builder_registry.configure(builder)


def resolve_view_container() -> ViewContainerFactory:
    """Return the default view container factory."""

    try:
        return _view_registry.resolve()
    except (ImportError, AttributeError) as exc:
        raise ContainerResolutionError("Unable to resolve default view container") from exc


def resolve_container_builder() -> ContainerBuilder:
    """Return the default runtime container builder."""

    try:
        return _builder_registry.resolve()
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

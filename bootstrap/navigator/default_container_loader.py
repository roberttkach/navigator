"""Default loader utilities for container collaborators."""
from __future__ import annotations

import os
from importlib import import_module
from typing import cast

from .container_errors import ContainerResolutionError
from .container_types import ContainerBuilder, ViewContainerFactory

DEFAULT_VIEW_CONTAINER_PATH = "navigator.infra.di.container.telegram:TelegramContainer"
DEFAULT_CONTAINER_BUILDER_PATH = "navigator.infra.di.container.builder:NavigatorContainerBuilder"
ENV_VIEW_CONTAINER = "NAVIGATOR_VIEW_CONTAINER"
ENV_CONTAINER_BUILDER = "NAVIGATOR_CONTAINER_BUILDER"


def default_view_loader() -> ViewContainerFactory:
    """Load the default view container factory declared via environment."""

    path = os.getenv(ENV_VIEW_CONTAINER, DEFAULT_VIEW_CONTAINER_PATH)
    container = _import_symbol(path)
    if not isinstance(container, type):
        raise ContainerResolutionError(
            f"Default view container '{path}' is not a container class"
        )
    return cast(ViewContainerFactory, container)


def default_builder_loader() -> ContainerBuilder:
    """Load the default container builder declared via environment."""

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
    "DEFAULT_CONTAINER_BUILDER_PATH",
    "DEFAULT_VIEW_CONTAINER_PATH",
    "ENV_CONTAINER_BUILDER",
    "ENV_VIEW_CONTAINER",
    "default_builder_loader",
    "default_view_loader",
]

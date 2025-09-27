"""Factories instantiating Navigator facades."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from .facade import NavigatorFacade

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


@dataclass(frozen=True)
class NavigatorFacadeFactory(Generic[FacadeT]):
    """Create navigator facades from assembled runtimes."""

    def create(self, runtime: "NavigatorRuntime", facade_type: Type[FacadeT]) -> FacadeT:
        return facade_type(runtime)


__all__ = ["NavigatorFacadeFactory"]


if False:  # pragma: no cover - typing only
    from .runtime import NavigatorRuntime

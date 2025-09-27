"""Service level ports describing runtime assembly behaviour."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeVar
from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .runtime import NavigatorRuntime

RequestT = TypeVar("RequestT", bound="RuntimeAssemblyRequest")


@dataclass(frozen=True)
class RuntimeAssemblyRequest:
    """Container describing runtime assembly inputs."""

    event: object
    state: object
    ledger: ViewLedger
    scope: Scope
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None
    missing_alert: MissingAlert | None = None
    overrides: NavigatorAssemblyOverrides | None = None
    resolution: "ContainerResolution" | None = None


class RuntimeAssemblyPort(Protocol[RequestT]):
    """Port for components capable of assembling navigator runtimes."""

    async def assemble(self, request: RequestT) -> NavigatorRuntime:
        """Assemble a runtime instance for the provided request."""


__all__ = [
    "RuntimeAssemblyPort",
    "RuntimeAssemblyRequest",
]


if TYPE_CHECKING:  # pragma: no cover - imported only for typing support
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution

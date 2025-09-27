"""Type contracts shared across navigator container orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from dependency_injector import containers
from typing import Protocol

from navigator.core.contracts import MissingAlert
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.core.telemetry import Telemetry

from .adapter import LedgerAdapter


ViewContainerFactory = type[containers.DeclarativeContainer]


class RuntimeSnapshotSource(Protocol):
    """Expose runtime snapshot creation capabilities."""

    def snapshot(self) -> NavigatorRuntimeSnapshot: ...


class RuntimeContainer(Protocol):
    """Expose runtime bindings required by bootstrap orchestration."""

    def runtime(self) -> RuntimeSnapshotSource: ...


@dataclass(frozen=True)
class ContainerRequest:
    """Payload required to build the runtime container."""

    event: object
    state: object
    ledger: LedgerAdapter
    alert: MissingAlert
    telemetry: Telemetry
    view_container: ViewContainerFactory


class ContainerBuilder(Protocol):
    """Protocol describing builders capable of producing runtime containers."""

    def build(self, request: ContainerRequest) -> RuntimeContainer: ...


__all__ = [
    "ContainerBuilder",
    "ContainerRequest",
    "RuntimeContainer",
    "RuntimeSnapshotSource",
    "ViewContainerFactory",
]

"""Factories building runtime assembly requests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .runtime_assembly_port import RuntimeAssemblyRequest


@dataclass(frozen=True)
class RuntimeAssemblyRequestFactory:
    """Create runtime assembly requests from presentation inputs."""

    def create(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None,
        missing_alert: MissingAlert | None,
        overrides: NavigatorAssemblyOverrides | None,
        resolution: "ContainerResolution" | None,
    ) -> RuntimeAssemblyRequest:
        return RuntimeAssemblyRequest(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=instrumentation,
            missing_alert=missing_alert,
            overrides=overrides,
            resolution=resolution,
        )


__all__ = ["RuntimeAssemblyRequestFactory"]


if False:  # pragma: no cover - typing only
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution

"""Bootstrap the Navigator runtime for telegram entrypoints."""
from __future__ import annotations

from .adapter import LedgerAdapter
from .assembly import NavigatorAssembler, assemble
from .container import ContainerFactory
from .context import BootstrapContext, scope_from_dto
from .runtime import ContainerRuntimeFactory, NavigatorFactory, NavigatorRuntimeBundle
from .telemetry import TelemetryFactory, calibrate_telemetry

__all__ = [
    "BootstrapContext",
    "ContainerFactory",
    "ContainerRuntimeFactory",
    "LedgerAdapter",
    "NavigatorAssembler",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
    "TelemetryFactory",
    "assemble",
    "calibrate_telemetry",
    "scope_from_dto",
]

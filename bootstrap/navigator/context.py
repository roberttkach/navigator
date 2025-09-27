"""Bootstrap context and DTO translation helpers."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .container_types import ViewContainerFactory


@dataclass(frozen=True)
class BootstrapContext:
    """Collect payloads required to assemble the navigator runtime."""

    event: object
    state: object
    ledger: ViewLedger
    scope: Scope
    missing_alert: MissingAlert | None = None
    view_container: ViewContainerFactory | None = None


__all__ = ["BootstrapContext", "ViewContainerFactory"]

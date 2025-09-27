"""Factories creating bootstrap contexts for runtime assembly."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .context import BootstrapContext, ViewContainerFactory


@dataclass(slots=True)
class BootstrapContextFactory:
    """Construct bootstrap context objects from raw payloads."""

    def create(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        missing_alert: MissingAlert | None,
        view_container: ViewContainerFactory | None,
    ) -> BootstrapContext:
        return BootstrapContext(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            missing_alert=missing_alert,
            view_container=view_container,
        )


__all__ = ["BootstrapContextFactory"]

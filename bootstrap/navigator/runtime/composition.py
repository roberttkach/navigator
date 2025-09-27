"""Compose navigator runtime services from provisioned artifacts."""
from __future__ import annotations

from typing import TYPE_CHECKING

from navigator.core.telemetry import Telemetry

from ..context import BootstrapContext
from ..telemetry import calibrate_telemetry
from .activation import (
    NavigatorRuntimeActivationBridge,
    RuntimeActivator,
)

if TYPE_CHECKING:
    from navigator.app.service.navigator_runtime import NavigatorRuntime
    from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot


class RuntimeCalibrator:
    """Bridge calibration utilities into a reusable collaborator."""

    def run(self, telemetry: Telemetry, snapshot: NavigatorRuntimeSnapshot) -> None:
        calibrate_telemetry(telemetry, snapshot.redaction)


class NavigatorRuntimeComposer:
    """Assemble navigator runtime services from container snapshots."""

    def __init__(self, activator: RuntimeActivator | None = None) -> None:
        self._activator = activator or NavigatorRuntimeActivationBridge()

    def compose(
        self,
        snapshot: NavigatorRuntimeSnapshot,
        context: BootstrapContext,
    ) -> NavigatorRuntime:
        plan = self._activator.create_plan(
            snapshot,
            context.scope,
            missing_alert=context.missing_alert,
        )
        return plan.activate()


__all__ = ["NavigatorRuntimeComposer", "RuntimeCalibrator"]

"""Compose navigator runtime services from provisioned artifacts."""
from __future__ import annotations

from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.app.service.navigator_runtime.activation import create_activation_plan
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.core.telemetry import Telemetry

from ..context import BootstrapContext, scope_from_dto
from ..telemetry import calibrate_telemetry


class RuntimeCalibrator:
    """Bridge calibration utilities into a reusable collaborator."""

    def run(self, telemetry: Telemetry, snapshot: NavigatorRuntimeSnapshot) -> None:
        calibrate_telemetry(telemetry, snapshot.redaction)


class NavigatorRuntimeComposer:
    """Assemble navigator runtime services from container snapshots."""

    def compose(
        self,
        snapshot: NavigatorRuntimeSnapshot,
        context: BootstrapContext,
    ) -> NavigatorRuntime:
        scope = scope_from_dto(context.scope)
        missing_alert = context.missing_alert
        plan = create_activation_plan(
            snapshot,
            scope,
            missing_alert=missing_alert,
        )
        return plan.activate()


__all__ = ["NavigatorRuntimeComposer", "RuntimeCalibrator"]

"""Compose navigator runtime services from provisioned artifacts."""
from __future__ import annotations

from navigator.app.service import build_navigator_runtime
from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
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
        dependencies: NavigatorDependencies = snapshot.dependencies
        scope = scope_from_dto(context.scope)
        missing_alert = context.missing_alert or dependencies.missing_alert
        return build_navigator_runtime(
            usecases=dependencies.usecases,
            scope=scope,
            guard=dependencies.guard,
            telemetry=dependencies.telemetry,
            missing_alert=missing_alert,
        )


__all__ = ["NavigatorRuntimeComposer", "RuntimeCalibrator"]

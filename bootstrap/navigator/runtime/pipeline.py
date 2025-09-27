"""Runtime assembly pipeline coordinating provision, calibration and composition."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.contracts import MissingAlert

from ..context import BootstrapContext, ViewContainerFactory
from ..telemetry import TelemetryFactory
from .bundle import NavigatorRuntimeBundle
from .composition import NavigatorRuntimeComposer, RuntimeCalibrator
from .provision import RuntimeProvision, RuntimeProvisioner, build_runtime_provisioner


@dataclass(frozen=True)
class RuntimeFactorySettings:
    """Group configuration required to assemble the runtime pipeline."""

    telemetry_factory: TelemetryFactory
    provisioner: RuntimeProvisioner
    calibrator: RuntimeCalibrator
    composer: NavigatorRuntimeComposer


class RuntimeAssemblyPipeline:
    """Execute the ordered steps required to produce a runtime bundle."""

    def __init__(self, settings: RuntimeFactorySettings) -> None:
        self._settings = settings

    def execute(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        provision = self._settings.provisioner.provision(context)
        self._calibrate(provision)
        runtime = self._settings.composer.compose(provision.snapshot, context)
        return NavigatorRuntimeBundle(
            telemetry=provision.telemetry,
            container=provision.container,
            runtime=runtime,
        )

    def _calibrate(self, provision: RuntimeProvision) -> None:
        self._settings.calibrator.run(provision.telemetry, provision.snapshot)


def build_runtime_pipeline(
    *,
    telemetry_factory: TelemetryFactory | None = None,
    missing_alert: MissingAlert | None = None,
    view_container: ViewContainerFactory | None = None,
    provisioner: RuntimeProvisioner | None = None,
    calibrator: RuntimeCalibrator | None = None,
    composer: NavigatorRuntimeComposer | None = None,
) -> RuntimeAssemblyPipeline:
    """Create an execution pipeline with sensible defaults."""

    factory = telemetry_factory or TelemetryFactory()
    resolved_provisioner = provisioner or build_runtime_provisioner(
        factory,
        missing_alert=missing_alert,
        view_container=view_container,
    )
    settings = RuntimeFactorySettings(
        telemetry_factory=factory,
        provisioner=resolved_provisioner,
        calibrator=calibrator or RuntimeCalibrator(),
        composer=composer or NavigatorRuntimeComposer(),
    )
    return RuntimeAssemblyPipeline(settings)


__all__ = [
    "RuntimeAssemblyPipeline",
    "RuntimeFactorySettings",
    "build_runtime_pipeline",
]

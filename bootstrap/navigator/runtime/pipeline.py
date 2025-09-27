"""Runtime assembly pipeline coordinating provision, calibration and composition."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
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
        provision = self._provision(context)
        calibrated = self._calibrate(provision)
        runtime = self._compose_runtime(calibrated, context)
        return self._package_bundle(calibrated, runtime)

    def _provision(self, context: BootstrapContext) -> RuntimeProvision:
        """Provision container, telemetry and snapshot for the given context."""

        return self._settings.provisioner.provision(context)

    def _calibrate(self, provision: RuntimeProvision) -> RuntimeProvision:
        """Calibrate telemetry using the provisioned snapshot."""

        self._settings.calibrator.run(provision.telemetry, provision.snapshot)
        return provision

    def _compose_runtime(
        self, provision: RuntimeProvision, context: BootstrapContext
    ) -> NavigatorRuntime:
        """Compose a runtime instance using the provisioned snapshot."""

        return self._settings.composer.compose(provision.snapshot, context)

    def _package_bundle(
        self, provision: RuntimeProvision, runtime: NavigatorRuntime
    ) -> NavigatorRuntimeBundle:
        """Bundle runtime, telemetry and container into a single artefact."""

        return NavigatorRuntimeBundle(
            telemetry=provision.telemetry,
            container=provision.container,
            runtime=runtime,
        )


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

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
class RuntimeProvisionStage:
    """Provision container, telemetry and snapshot."""

    provisioner: RuntimeProvisioner

    def run(self, context: BootstrapContext) -> RuntimeProvision:
        return self.provisioner.provision(context)


@dataclass(frozen=True)
class RuntimeCalibrationStage:
    """Calibrate telemetry after the provision step."""

    calibrator: RuntimeCalibrator

    def run(self, provision: RuntimeProvision) -> RuntimeProvision:
        self.calibrator.run(provision.telemetry, provision.snapshot)
        return provision


@dataclass(frozen=True)
class RuntimeCompositionStage:
    """Compose the runtime instance from provisioned artefacts."""

    composer: NavigatorRuntimeComposer

    def run(self, provision: RuntimeProvision, context: BootstrapContext) -> NavigatorRuntime:
        return self.composer.compose(provision.snapshot, context)


@dataclass(frozen=True)
class RuntimePackagingStage:
    """Package calibration results and runtime into a bundle."""

    def package(self, provision: RuntimeProvision, runtime: NavigatorRuntime) -> NavigatorRuntimeBundle:
        return NavigatorRuntimeBundle(
            telemetry=provision.telemetry,
            container=provision.container,
            runtime=runtime,
        )


@dataclass(frozen=True)
class RuntimeFactorySettings:
    """Group the stages required to assemble the runtime pipeline."""

    provision: RuntimeProvisionStage
    calibration: RuntimeCalibrationStage
    composition: RuntimeCompositionStage
    packaging: RuntimePackagingStage


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

        return self._settings.provision.run(context)

    def _calibrate(self, provision: RuntimeProvision) -> RuntimeProvision:
        """Calibrate telemetry using the provisioned snapshot."""

        return self._settings.calibration.run(provision)

    def _compose_runtime(
        self, provision: RuntimeProvision, context: BootstrapContext
    ) -> NavigatorRuntime:
        """Compose a runtime instance using the provisioned snapshot."""

        return self._settings.composition.run(provision, context)

    def _package_bundle(
        self, provision: RuntimeProvision, runtime: NavigatorRuntime
    ) -> NavigatorRuntimeBundle:
        """Bundle runtime, telemetry and container into a single artefact."""

        return self._settings.packaging.package(provision, runtime)


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
        provision=RuntimeProvisionStage(resolved_provisioner),
        calibration=RuntimeCalibrationStage(calibrator or RuntimeCalibrator()),
        composition=RuntimeCompositionStage(composer or NavigatorRuntimeComposer()),
        packaging=RuntimePackagingStage(),
    )
    return RuntimeAssemblyPipeline(settings)


__all__ = [
    "RuntimeCalibrationStage",
    "RuntimeCompositionStage",
    "RuntimePackagingStage",
    "RuntimeAssemblyPipeline",
    "RuntimeFactorySettings",
    "RuntimeProvisionStage",
    "build_runtime_pipeline",
]

"""Factories creating navigator runtime bundles."""
from __future__ import annotations

from typing import Protocol

from navigator.app.service.navigator_runtime import MissingAlert

from ..context import BootstrapContext, ViewContainerFactory
from ..telemetry import TelemetryFactory
from .bundle import NavigatorRuntimeBundle
from .composition import NavigatorRuntimeComposer, RuntimeCalibrator
from .provision import RuntimeProvisioner, build_runtime_provisioner


class NavigatorFactory(Protocol):
    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        """Create a navigator runtime bundle for the provided context."""


class ContainerRuntimeFactory(NavigatorFactory):
    """Create navigators backed by the dependency injection container."""

    def __init__(
        self,
        telemetry_factory: TelemetryFactory | None = None,
        missing_alert: MissingAlert | None = None,
        *,
        view_container: ViewContainerFactory | None = None,
        provisioner: RuntimeProvisioner | None = None,
        calibrator: RuntimeCalibrator | None = None,
        composer: NavigatorRuntimeComposer | None = None,
    ) -> None:
        factory = telemetry_factory or TelemetryFactory()
        self._provisioner = provisioner or build_runtime_provisioner(
            factory,
            missing_alert=missing_alert,
            view_container=view_container,
        )
        self._calibrator = calibrator or RuntimeCalibrator()
        self._composer = composer or NavigatorRuntimeComposer()

    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        provision = self._provisioner.provision(context)
        self._calibrator.run(provision.telemetry, provision.snapshot)
        runtime = self._composer.compose(provision.snapshot, context)
        return NavigatorRuntimeBundle(
            telemetry=provision.telemetry,
            container=provision.container,
            runtime=runtime,
        )


__all__ = ["ContainerRuntimeFactory", "NavigatorFactory"]

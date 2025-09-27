"""Factories creating navigator runtime bundles."""
from __future__ import annotations

from typing import Protocol

from navigator.core.contracts import MissingAlert

from ..context import BootstrapContext, ViewContainerFactory
from ..telemetry import TelemetryFactory
from .bundle import NavigatorRuntimeBundle
from .composition import NavigatorRuntimeComposer, RuntimeCalibrator
from .pipeline import RuntimeAssemblyPipeline, build_runtime_pipeline
from .provision import RuntimeProvisioner


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
        self._pipeline = build_runtime_pipeline(
            telemetry_factory=telemetry_factory,
            missing_alert=missing_alert,
            view_container=view_container,
            provisioner=provisioner,
            calibrator=calibrator,
            composer=composer,
        )

    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        return self._pipeline.execute(context)


__all__ = ["ContainerRuntimeFactory", "NavigatorFactory"]

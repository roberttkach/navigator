"""Runtime assembly factories tying together telemetry, container and facade."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.app.service import build_navigator_runtime
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer
from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies

from .context import BootstrapContext, scope_from_dto
from .container import ContainerFactory
from .inspection import inspect_container
from .telemetry import TelemetryFactory, calibrate_telemetry
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot


@dataclass(frozen=True)
class RuntimeProvision:
    """Capture the intermediate components produced during bootstrap."""

    telemetry: Telemetry
    container: AppContainer
    snapshot: NavigatorRuntimeSnapshot


class TelemetryInitializer:
    """Create telemetry instances isolated from provisioning orchestration."""

    def __init__(self, factory: TelemetryFactory) -> None:
        self._factory = factory

    def initialize(self) -> Telemetry:
        return self._factory.create()


class ContainerAssembler:
    """Build dependency injection containers for navigator runtime."""

    def __init__(self, *, missing_alert: MissingAlert | None = None) -> None:
        self._missing_alert = missing_alert

    def assemble(self, telemetry: Telemetry, context: BootstrapContext) -> AppContainer:
        factory = ContainerFactory(telemetry, alert=self._missing_alert)
        return factory.create(context)


class ContainerInspector:
    """Produce container diagnostics independently from provisioning."""

    def inspect(self, container: AppContainer) -> NavigatorRuntimeSnapshot:
        return inspect_container(container)


class RuntimeProvisioner:
    """Produce the container, telemetry and inspection snapshot."""

    def __init__(
        self,
        telemetry_factory: TelemetryFactory,
        *,
        missing_alert: MissingAlert | None = None,
        initializer: TelemetryInitializer | None = None,
        assembler: ContainerAssembler | None = None,
        inspector: ContainerInspector | None = None,
    ) -> None:
        self._initializer = initializer or TelemetryInitializer(telemetry_factory)
        self._assembler = assembler or ContainerAssembler(missing_alert=missing_alert)
        self._inspector = inspector or ContainerInspector()

    def provision(self, context: BootstrapContext) -> RuntimeProvision:
        telemetry = self._initializer.initialize()
        container = self._assembler.assemble(telemetry, context)
        snapshot = self._inspector.inspect(container)
        return RuntimeProvision(telemetry=telemetry, container=container, snapshot=snapshot)


class RuntimeCalibrator:
    """Bridge calibration utilities into a reusable collaborator."""

    def run(self, telemetry: Telemetry, snapshot: NavigatorRuntimeSnapshot) -> None:
        calibrate_telemetry(telemetry, snapshot.redaction)


class NavigatorRuntimeComposer:
    """Assemble navigator runtime services from container snapshots."""

    def compose(
        self, snapshot: NavigatorRuntimeSnapshot, context: BootstrapContext
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


@dataclass(frozen=True)
class NavigatorRuntimeBundle:
    """Aggregate runtime services exposed to bootstrap instrumentation."""

    telemetry: Telemetry
    container: AppContainer
    runtime: NavigatorRuntime


class NavigatorFactory(Protocol):
    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle: ...


class ContainerRuntimeFactory(NavigatorFactory):
    """Create navigators backed by the dependency injection container."""

    def __init__(
        self,
        telemetry_factory: TelemetryFactory | None = None,
        missing_alert: MissingAlert | None = None,
        *,
        provisioner: RuntimeProvisioner | None = None,
        calibrator: RuntimeCalibrator | None = None,
        composer: NavigatorRuntimeComposer | None = None,
    ) -> None:
        factory = telemetry_factory or TelemetryFactory()
        self._provisioner = provisioner or RuntimeProvisioner(
            factory,
            missing_alert=missing_alert,
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


__all__ = [
    "ContainerAssembler",
    "ContainerInspector",
    "ContainerRuntimeFactory",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
    "RuntimeProvision",
    "RuntimeProvisioner",
    "TelemetryInitializer",
]

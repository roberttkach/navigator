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


class RuntimeProvisioner:
    """Produce the container, telemetry and inspection snapshot."""

    def __init__(
        self,
        telemetry_factory: TelemetryFactory,
        *,
        missing_alert: MissingAlert | None = None,
    ) -> None:
        self._telemetry_factory = telemetry_factory
        self._missing_alert = missing_alert

    def provision(self, context: BootstrapContext) -> RuntimeProvision:
        telemetry = self._telemetry_factory.create()
        container = ContainerFactory(telemetry, alert=self._missing_alert).create(context)
        snapshot = inspect_container(container)
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
    "ContainerRuntimeFactory",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
    "RuntimeProvision",
    "RuntimeProvisioner",
]

"""Runtime assembly factories tying together telemetry, container and facade."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer
from navigator.presentation.bootstrap.navigator import NavigatorDependencies, compose
from navigator.presentation.navigator import Navigator

from .context import BootstrapContext, scope_from_dto
from .container import ContainerFactory
from .inspection import NavigatorContainerSnapshot, inspect_container
from .telemetry import TelemetryFactory, calibrate_telemetry


@dataclass(frozen=True)
class NavigatorRuntimeBundle:
    """Aggregate runtime services exposed to bootstrap instrumentation."""

    telemetry: Telemetry
    container: AppContainer
    navigator: Navigator


class NavigatorFactory(Protocol):
    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle: ...


class ContainerRuntimeFactory(NavigatorFactory):
    """Create navigators backed by the dependency injection container."""

    def __init__(
        self,
        telemetry_factory: TelemetryFactory | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> None:
        self._telemetry_factory = telemetry_factory or TelemetryFactory()
        self._missing_alert = missing_alert

    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        telemetry = self._create_telemetry()
        container = self._create_container(context, telemetry)
        snapshot = inspect_container(container)
        self._calibrate(telemetry, snapshot)
        navigator = self._compose_navigator(snapshot, context)
        return NavigatorRuntimeBundle(telemetry=telemetry, container=container, navigator=navigator)

    def _create_telemetry(self) -> Telemetry:
        return self._telemetry_factory.create()

    def _create_container(self, context: BootstrapContext, telemetry: Telemetry) -> AppContainer:
        factory = ContainerFactory(telemetry, alert=self._missing_alert)
        return factory.create(context)

    def _calibrate(self, telemetry: Telemetry, snapshot: NavigatorContainerSnapshot) -> None:
        calibrate_telemetry(telemetry, snapshot.redaction)

    def _compose_navigator(
        self, snapshot: NavigatorContainerSnapshot, context: BootstrapContext
    ) -> Navigator:
        dependencies: NavigatorDependencies = snapshot.dependencies
        return compose(
            dependencies,
            scope_from_dto(context.scope),
            missing_alert=context.missing_alert,
        )


__all__ = [
    "ContainerRuntimeFactory",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
]

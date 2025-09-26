"""Runtime assembly factories tying together telemetry, container and facade."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer
from navigator.presentation.bootstrap.navigator import compose
from navigator.presentation.navigator import Navigator

from .context import BootstrapContext, scope_from_dto
from .container import ContainerFactory
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
        telemetry = self._telemetry_factory.create()
        container = ContainerFactory(telemetry, alert=self._missing_alert).create(context)
        core = container.core()
        settings = core.settings()
        calibrate_telemetry(telemetry, getattr(settings, "redaction", ""))
        navigator = compose(
            container,
            scope_from_dto(context.scope),
            missing_alert=core.alert(),
        )
        return NavigatorRuntimeBundle(telemetry=telemetry, container=container, navigator=navigator)


__all__ = [
    "ContainerRuntimeFactory",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
]

"""Concrete container builder wiring the application composition root."""
from __future__ import annotations

from navigator.bootstrap.navigator.container_types import ContainerBuilder, ContainerRequest

from . import AppContainer, CoreBindings, IntegrationBindings, RuntimeBindings, UseCaseBindings


class NavigatorContainerBuilder(ContainerBuilder):
    """Build navigator containers using dependency-injector bindings."""

    def build(self, request: ContainerRequest) -> AppContainer:
        core = CoreBindings(
            event=request.event,
            state=request.state,
            ledger=request.ledger,
            alert=request.alert,
            telemetry=request.telemetry,
        )
        integration = IntegrationBindings(
            core=core,
            telemetry=request.telemetry,
            view_container=request.view_container,
        )
        usecases = UseCaseBindings(
            core=core,
            integration=integration,
            telemetry=request.telemetry,
        )
        runtime = RuntimeBindings(
            core=core,
            usecases=usecases,
            telemetry=request.telemetry,
        )
        return AppContainer(
            core=core,
            integration=integration,
            usecases=usecases,
            runtime_bindings=runtime,
        )


__all__ = ["NavigatorContainerBuilder"]

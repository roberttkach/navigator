"""Concrete container builder wiring the application composition root."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.bootstrap.navigator.container_types import ContainerBuilder, ContainerRequest

from . import AppContainer, CoreBindings, IntegrationBindings, RuntimeBindings, UseCaseBindings


class CoreFactory(Protocol):
    """Build the core binding layer from an incoming request."""

    def __call__(self, request: ContainerRequest) -> CoreBindings: ...


class IntegrationFactory(Protocol):
    """Build the integration bindings using the core layer."""

    def __call__(
        self,
        *,
        core: CoreBindings,
        request: ContainerRequest,
    ) -> IntegrationBindings: ...


class UseCaseFactory(Protocol):
    """Build use case bindings from the core and integration layers."""

    def __call__(
        self,
        *,
        core: CoreBindings,
        integration: IntegrationBindings,
        request: ContainerRequest,
    ) -> UseCaseBindings: ...


class RuntimeFactory(Protocol):
    """Build runtime bindings from the core and use case layers."""

    def __call__(
        self,
        *,
        core: CoreBindings,
        usecases: UseCaseBindings,
        request: ContainerRequest,
    ) -> RuntimeBindings: ...


class AppContainerFactory(Protocol):
    """Assemble the public application container from layer bindings."""

    def __call__(
        self,
        *,
        core: CoreBindings,
        integration: IntegrationBindings,
        usecases: UseCaseBindings,
        runtime: RuntimeBindings,
    ) -> AppContainer: ...


@dataclass(frozen=True)
class ContainerAssemblyPlan:
    """Describe how to assemble the layered navigator container."""

    core: CoreFactory
    integration: IntegrationFactory
    usecases: UseCaseFactory
    runtime: RuntimeFactory
    app: AppContainerFactory

    def build(self, request: ContainerRequest) -> AppContainer:
        """Execute the plan and return the assembled container."""

        core = self.core(request)
        integration = self.integration(core=core, request=request)
        usecases = self.usecases(core=core, integration=integration, request=request)
        runtime = self.runtime(core=core, usecases=usecases, request=request)
        return self.app(core=core, integration=integration, usecases=usecases, runtime=runtime)


def _default_core_factory(request: ContainerRequest) -> CoreBindings:
    return CoreBindings(
        event=request.event,
        state=request.state,
        ledger=request.ledger,
        alert=request.alert,
        telemetry=request.telemetry,
    )


def _default_integration_factory(
    *, core: CoreBindings, request: ContainerRequest
) -> IntegrationBindings:
    return IntegrationBindings(
        core=core,
        telemetry=request.telemetry,
        view_container=request.view_container,
    )


def _default_usecase_factory(
    *, core: CoreBindings, integration: IntegrationBindings, request: ContainerRequest
) -> UseCaseBindings:
    return UseCaseBindings(core=core, integration=integration, telemetry=request.telemetry)


def _default_runtime_factory(
    *, core: CoreBindings, usecases: UseCaseBindings, request: ContainerRequest
) -> RuntimeBindings:
    return RuntimeBindings(core=core, usecases=usecases, telemetry=request.telemetry)


def _default_app_factory(
    *,
    core: CoreBindings,
    integration: IntegrationBindings,
    usecases: UseCaseBindings,
    runtime: RuntimeBindings,
) -> AppContainer:
    return AppContainer(
        core=core,
        integration=integration,
        usecases=usecases,
        runtime_bindings=runtime,
    )


def _create_default_plan() -> ContainerAssemblyPlan:
    return ContainerAssemblyPlan(
        core=_default_core_factory,
        integration=_default_integration_factory,
        usecases=_default_usecase_factory,
        runtime=_default_runtime_factory,
        app=_default_app_factory,
    )


class NavigatorContainerBuilder(ContainerBuilder):
    """Build navigator containers using dependency-injector bindings."""

    def __init__(self, plan: ContainerAssemblyPlan | None = None) -> None:
        self._plan = plan or _create_default_plan()

    def build(self, request: ContainerRequest) -> AppContainer:
        return self._plan.build(request)


__all__ = ["NavigatorContainerBuilder"]

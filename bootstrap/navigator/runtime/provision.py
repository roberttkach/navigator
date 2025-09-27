"""Provision utilities for assembling the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.core.telemetry import Telemetry

from ..context import BootstrapContext, ViewContainerFactory
from ..container import ContainerFactory
from ..container_types import ContainerBuilder, RuntimeContainer
from ..inspection import inspect_container
from ..telemetry import TelemetryFactory


@dataclass(frozen=True)
class RuntimeProvision:
    """Capture the intermediate components produced during bootstrap."""

    telemetry: Telemetry
    container: RuntimeContainer
    snapshot: NavigatorRuntimeSnapshot


class TelemetryInitializer:
    """Create telemetry instances isolated from provisioning orchestration."""

    def __init__(self, factory: TelemetryFactory) -> None:
        self._factory = factory

    def initialize(self) -> Telemetry:
        return self._factory.create()


class ContainerAssembler:
    """Build dependency injection containers for navigator runtime."""

    def __init__(
        self,
        *,
        missing_alert: MissingAlert | None = None,
        view_container: ViewContainerFactory | None = None,
        builder: ContainerBuilder | None = None,
    ) -> None:
        self._missing_alert = missing_alert
        self._view_container = view_container
        self._builder = builder

    def assemble(self, telemetry: Telemetry, context: BootstrapContext) -> RuntimeContainer:
        factory = ContainerFactory(
            telemetry,
            alert=self._missing_alert,
            view_container=self._view_container,
            builder=self._builder,
        )
        return factory.create(context)


class ContainerInspector:
    """Produce container diagnostics independently from provisioning."""

    def inspect(self, container: RuntimeContainer) -> NavigatorRuntimeSnapshot:
        return inspect_container(container)


@dataclass(slots=True)
class RuntimeProvisionWorkflow:
    """Execute the telemetry/container/inspection sequence as a single unit."""

    initializer: TelemetryInitializer
    assembler: ContainerAssembler
    inspector: ContainerInspector

    def run(self, context: BootstrapContext) -> RuntimeProvision:
        telemetry = self.initializer.initialize()
        container = self.assembler.assemble(telemetry, context)
        snapshot = self.inspector.inspect(container)
        return RuntimeProvision(telemetry=telemetry, container=container, snapshot=snapshot)


class RuntimeProvisioner:
    """Produce the container, telemetry and inspection snapshot."""

    def __init__(self, workflow: RuntimeProvisionWorkflow) -> None:
        self._workflow = workflow

    def provision(self, context: BootstrapContext) -> RuntimeProvision:
        return self._workflow.run(context)


def build_runtime_provisioner(
    telemetry_factory: TelemetryFactory,
    *,
    missing_alert: MissingAlert | None = None,
    view_container: ViewContainerFactory | None = None,
    builder: ContainerBuilder | None = None,
    initializer: TelemetryInitializer | None = None,
    assembler: ContainerAssembler | None = None,
    inspector: ContainerInspector | None = None,
) -> RuntimeProvisioner:
    """Create a provisioner backed by the default workflow collaborators."""

    init = initializer or TelemetryInitializer(telemetry_factory)
    assemble = assembler or ContainerAssembler(
        missing_alert=missing_alert,
        view_container=view_container,
        builder=builder,
    )
    review = inspector or ContainerInspector()
    workflow = RuntimeProvisionWorkflow(init, assemble, review)
    return RuntimeProvisioner(workflow)


__all__ = [
    "ContainerAssembler",
    "ContainerInspector",
    "RuntimeProvision",
    "build_runtime_provisioner",
    "RuntimeProvisioner",
    "RuntimeProvisionWorkflow",
    "TelemetryInitializer",
]

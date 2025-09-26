"""Assemble collaborators that drive edit execution."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.core.port.message import MessageGateway
from navigator.core.telemetry import Telemetry

from .cleanup import EditCleanup
from .dispatcher import VerdictDispatcher
from .error import EditErrorHandler
from .fallback import FallbackStrategy
from .operation import EditOperation
from .refiner import MetaRefiner
from .telemetry import EditTelemetry


@dataclass(slots=True)
class EditComponents:
    """Aggregate edit collaborators exposed to the executor."""

    operation: EditOperation
    cleanup: EditCleanup
    refiner: MetaRefiner


@dataclass(frozen=True)
class EditComponentDependencies:
    """Core dependencies required to assemble edit collaborators."""

    gateway: MessageGateway
    telemetry: Telemetry


@dataclass(frozen=True)
class EditComponentOverrides:
    """Optional overrides replacing individual collaborators."""

    dispatcher: VerdictDispatcher | None = None
    errors: EditErrorHandler | None = None
    refiner: MetaRefiner | None = None
    cleanup: EditCleanup | None = None


class EditCollaboratorFactory:
    """Build individual collaborators required by edit execution."""

    def __init__(self, dependencies: EditComponentDependencies) -> None:
        self._gateway = dependencies.gateway
        self._telemetry = dependencies.telemetry

    def fallback(self) -> FallbackStrategy:
        return FallbackStrategy(self._gateway)

    def dispatcher(self, fallback: FallbackStrategy) -> VerdictDispatcher:
        return VerdictDispatcher(self._gateway, fallback=fallback)

    def error_handler(self, fallback: FallbackStrategy) -> EditErrorHandler:
        telemetry_helper = EditTelemetry(self._telemetry)
        return EditErrorHandler(telemetry_helper, fallback)

    def cleanup(self) -> EditCleanup:
        return EditCleanup(self._gateway)

    def refiner(self) -> MetaRefiner:
        return MetaRefiner()


class EditComponentAssembler:
    """Compose edit execution collaborators through the dedicated factory."""

    def __init__(self, factory: EditCollaboratorFactory) -> None:
        self._factory = factory

    def assemble(self, overrides: EditComponentOverrides | None = None) -> EditComponents:
        options = overrides or EditComponentOverrides()
        fallback = self._factory.fallback()
        dispatcher = options.dispatcher or self._factory.dispatcher(fallback)
        handler = options.errors or self._factory.error_handler(fallback)
        cleanup = options.cleanup or self._factory.cleanup()
        refiner = options.refiner or self._factory.refiner()
        operation = EditOperation(dispatcher, handler)
        return EditComponents(operation=operation, cleanup=cleanup, refiner=refiner)


def build_edit_components(
    gateway: MessageGateway,
    telemetry: Telemetry,
    *,
    dispatcher: VerdictDispatcher | None = None,
    errors: EditErrorHandler | None = None,
    refiner: MetaRefiner | None = None,
    cleanup: EditCleanup | None = None,
) -> EditComponents:
    """Assemble edit collaborators using optional overrides."""

    dependencies = EditComponentDependencies(gateway=gateway, telemetry=telemetry)
    factory = EditCollaboratorFactory(dependencies)
    overrides = EditComponentOverrides(
        dispatcher=dispatcher,
        errors=errors,
        refiner=refiner,
        cleanup=cleanup,
    )
    assembler = EditComponentAssembler(factory)
    return assembler.assemble(overrides)


__all__ = [
    "EditCollaboratorFactory",
    "EditComponentAssembler",
    "EditComponentDependencies",
    "EditComponentOverrides",
    "EditComponents",
    "build_edit_components",
]


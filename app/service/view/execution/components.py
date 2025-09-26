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


class EditComponentAssembler:
    """Compose edit execution collaborators with explicit steps."""

    def __init__(self, dependencies: EditComponentDependencies) -> None:
        self._gateway = dependencies.gateway
        self._telemetry = dependencies.telemetry

    def assemble(self, overrides: EditComponentOverrides | None = None) -> EditComponents:
        options = overrides or EditComponentOverrides()
        fallback = self._build_fallback()
        dispatcher = options.dispatcher or self._build_dispatcher(fallback)
        handler = options.errors or self._build_error_handler(fallback)
        cleanup = options.cleanup or self._build_cleanup()
        refiner = options.refiner or self._build_refiner()
        operation = EditOperation(dispatcher, handler)
        return EditComponents(operation=operation, cleanup=cleanup, refiner=refiner)

    def _build_fallback(self) -> FallbackStrategy:
        return FallbackStrategy(self._gateway)

    def _build_dispatcher(
        self, fallback: FallbackStrategy
    ) -> VerdictDispatcher:
        return VerdictDispatcher(self._gateway, fallback=fallback)

    def _build_error_handler(
        self, fallback: FallbackStrategy
    ) -> EditErrorHandler:
        telemetry_helper = EditTelemetry(self._telemetry)
        return EditErrorHandler(telemetry_helper, fallback)

    def _build_cleanup(self) -> EditCleanup:
        return EditCleanup(self._gateway)

    def _build_refiner(self) -> MetaRefiner:
        return MetaRefiner()


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
    overrides = EditComponentOverrides(
        dispatcher=dispatcher,
        errors=errors,
        refiner=refiner,
        cleanup=cleanup,
    )
    assembler = EditComponentAssembler(dependencies)
    return assembler.assemble(overrides)


__all__ = [
    "EditComponentAssembler",
    "EditComponentDependencies",
    "EditComponentOverrides",
    "EditComponents",
    "build_edit_components",
]


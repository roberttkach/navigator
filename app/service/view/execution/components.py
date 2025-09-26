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

    fallback = FallbackStrategy(gateway)
    telemetry_helper = EditTelemetry(telemetry)
    dispatch = dispatcher or VerdictDispatcher(gateway, fallback=fallback)
    handler = errors or EditErrorHandler(telemetry_helper, fallback)
    cleaner = cleanup or EditCleanup(gateway)
    meta = refiner or MetaRefiner()
    operation = EditOperation(dispatch, handler)
    return EditComponents(operation=operation, cleanup=cleaner, refiner=meta)


__all__ = ["EditComponents", "build_edit_components"]


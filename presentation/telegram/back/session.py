"""Telemetry session helpers for retreat orchestration."""
from __future__ import annotations

from aiogram.types import CallbackQuery

from .telemetry import RetreatTelemetry


class TelemetryScopeSession:
    """Encapsulate telemetry interactions for a single retreat execution."""

    def __init__(self, telemetry: RetreatTelemetry, scope: object) -> None:
        self._telemetry = telemetry
        self._scope = scope

    def enter(self) -> None:
        self._telemetry.entered(self._scope)

    def complete(self) -> None:
        self._telemetry.completed(self._scope)

    def fail(self, note: str) -> None:
        self._telemetry.failed(note, self._scope)


class TelemetryScopeFactory:
    """Create telemetry sessions decoupled from orchestrator logic."""

    def __init__(self, telemetry: RetreatTelemetry) -> None:
        self._telemetry = telemetry

    def start(self, cb: CallbackQuery) -> TelemetryScopeSession:
        session = TelemetryScopeSession(
            self._telemetry,
            self._telemetry.scope(cb),
        )
        session.enter()
        return session


__all__ = ["TelemetryScopeFactory", "TelemetryScopeSession"]

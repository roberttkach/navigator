"""Telemetry-aware orchestration for retreat workflows."""

from __future__ import annotations

from collections.abc import Mapping

from aiogram.types import CallbackQuery

from .protocols import NavigatorBack
from .result import RetreatResult
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


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


class RetreatFailurePolicy:
    """Translate unexpected workflow errors into retreat outcomes."""

    def __init__(self, default_note: str = "generic") -> None:
        self._default_note = default_note

    def handle(self, error: Exception) -> RetreatResult:
        del error  # defensive branch - logging handled upstream
        return RetreatResult.failed(self._default_note)


class RetreatOutcomeReporter:
    """Report workflow outcomes through telemetry sessions."""

    def __init__(self, default_note: str = "generic") -> None:
        self._default_note = default_note

    def report(self, result: RetreatResult, session: TelemetryScopeSession) -> RetreatResult:
        if result.success:
            session.complete()
        else:
            session.fail(result.note or self._default_note)
        return result


class RetreatWorkflowRunner:
    """Execute workflow logic while delegating failure handling."""

    def __init__(self, workflow: RetreatWorkflow, failures: RetreatFailurePolicy) -> None:
        self._workflow = workflow
        self._failures = failures

    async def run(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> RetreatResult:
        try:
            return await self._workflow.execute(cb, navigator, payload)
        except Exception as error:  # pragma: no cover - defensive net for logging
            return self._failures.handle(error)


class RetreatOrchestrator:
    """Drive retreat workflow execution with dedicated collaborators."""

    def __init__(
        self,
        *,
        telemetry: TelemetryScopeFactory,
        runner: RetreatWorkflowRunner,
        reporter: RetreatOutcomeReporter,
    ) -> None:
        self._telemetry = telemetry
        self._runner = runner
        self._reporter = reporter

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> RetreatResult:
        session = self._telemetry.start(cb)
        result = await self._runner.run(cb, navigator, payload)
        return self._reporter.report(result, session)


__all__ = [
    "RetreatFailurePolicy",
    "RetreatOrchestrator",
    "RetreatOutcomeReporter",
    "RetreatWorkflowRunner",
    "TelemetryScopeFactory",
    "TelemetryScopeSession",
]

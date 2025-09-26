"""Telemetry-aware orchestration for retreat workflows."""

from __future__ import annotations

from aiogram.types import CallbackQuery

from .protocols import NavigatorBack
from .result import RetreatResult
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


class RetreatOrchestrator:
    """Drive retreat workflow execution with telemetry orchestration."""

    def __init__(
        self,
        *,
        telemetry: RetreatTelemetry,
        workflow: RetreatWorkflow,
    ) -> None:
        self._telemetry = telemetry
        self._workflow = workflow

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, object],
    ) -> RetreatResult:
        scope = self._telemetry.scope(cb)
        self._telemetry.entered(scope)
        try:
            result = await self._workflow.execute(cb, navigator, payload)
        except Exception:  # pragma: no cover - defensive net for logging
            self._telemetry.failed("generic", scope)
            return RetreatResult.failed("generic")

        if result.success:
            self._telemetry.completed(scope)
        else:
            self._telemetry.failed(result.note or "generic", scope)
        return result


__all__ = ["RetreatOrchestrator"]

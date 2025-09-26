"""Adapters exposing telegram retreat orchestration."""

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery

from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcome, RetreatOutcomeFactory
from .protocols import NavigatorBack


class RetreatHandler:
    """Adapt retreat workflow results to Telegram specific outcomes."""

    def __init__(
        self,
        orchestrator: RetreatOrchestrator,
        outcomes: RetreatOutcomeFactory,
    ) -> None:
        self._orchestrator = orchestrator
        self._outcomes = outcomes

    async def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatOutcome:
        result = await self._orchestrator.execute(cb, navigator, payload)
        return self._outcomes.render(result, cb)


__all__ = ["RetreatHandler"]

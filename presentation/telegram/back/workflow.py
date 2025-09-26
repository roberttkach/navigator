"""Workflow coordination for telegram retreat operations."""

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery

from navigator.app.service.retreat_failure import RetreatFailureResolver

from .context import RetreatContextBuilder
from .protocols import NavigatorBack
from .result import RetreatResult


class RetreatWorkflow:
    """Drive navigator back actions while building execution context."""

    def __init__(
        self,
        *,
        context: RetreatContextBuilder,
        failures: RetreatFailureResolver,
    ) -> None:
        self._context = context
        self._failures = failures

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatResult:
        try:
            context = self._context.build(cb, payload)
            await navigator.back(context=context)
        except Exception as error:  # pragma: no cover - mapper branch
            note = self._failures.translate(error)
            if note is None:
                raise
            return RetreatResult.failed(note)
        return RetreatResult.ok()


__all__ = ["RetreatWorkflow"]

"""Workflow coordination for telegram retreat operations."""

from __future__ import annotations

from collections.abc import Mapping

from aiogram.types import CallbackQuery

from navigator.core.contracts.back import NavigatorBackContext
from navigator.app.service.retreat_failure import RetreatFailureResolver

from .context import RetreatContextBuilder
from .protocols import NavigatorBack
from .result import RetreatResult


class RetreatBackExecutor:
    """Construct navigator contexts and invoke retreat operations."""

    def __init__(self, context: RetreatContextBuilder) -> None:
        self._context = context

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> None:
        context: NavigatorBackContext = self._context.build(cb, payload)
        await navigator.history.back(context=context)


class RetreatFailureHandler:
    """Translate application failures into user-facing retreat results."""

    def __init__(self, resolver: RetreatFailureResolver) -> None:
        self._resolver = resolver

    def handle(self, error: Exception) -> RetreatResult | None:
        note = self._resolver.translate(error)
        if note is None:
            return None
        return RetreatResult.failed(note)


class RetreatWorkflow:
    """Drive navigator back actions while delegating policies to collaborators."""

    def __init__(
        self,
        *,
        executor: RetreatBackExecutor,
        failures: RetreatFailureHandler,
    ) -> None:
        self._executor = executor
        self._failures = failures

    @classmethod
    def from_builders(
        cls,
        *,
        context: RetreatContextBuilder,
        failures: RetreatFailureResolver,
    ) -> "RetreatWorkflow":
        return cls(
            executor=RetreatBackExecutor(context),
            failures=RetreatFailureHandler(failures),
        )

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> RetreatResult:
        try:
            await self._executor.execute(cb, navigator, payload)
        except Exception as error:  # pragma: no cover - mapper branch
            result = self._failures.handle(error)
            if result is None:
                raise
            return result
        return RetreatResult.ok()


__all__ = [
    "RetreatBackExecutor",
    "RetreatFailureHandler",
    "RetreatWorkflow",
]

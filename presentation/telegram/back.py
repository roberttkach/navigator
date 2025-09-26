"""Domain-aware helpers for Telegram retreat handling."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from aiogram.types import CallbackQuery

from navigator.core.error import HistoryEmpty, InlineUnsupported, StateNotFound
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class NavigatorBack(Protocol):
    async def back(self, context: dict[str, Any]) -> None: ...


Translator = Callable[[str, str], str]


@dataclass(frozen=True)
class RetreatOutcome:
    """Represents Telegram answer parameters for retreat operations."""

    text: str | None = None
    show_alert: bool = False


class RetreatTelemetry:
    """Isolate telemetry emission for retreat lifecycle events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def scope(self, cb: CallbackQuery) -> dict[str, object]:
        return {
            "chat": cb.message.chat.id if cb.message else 0,
            "inline": bool(cb.inline_message_id),
        }

    def entered(self, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_ENTER,
            kind="callback",
            scope=scope,
        )

    def completed(self, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_DONE,
            kind="callback",
            scope=scope,
        )

    def failed(self, note: str, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.WARNING,
            LogCode.ROUTER_BACK_FAIL,
            kind="callback",
            note=note,
            scope=scope,
        )


class RetreatContextBuilder:
    """Create navigator context payloads for retreat execution."""

    def build(self, cb: CallbackQuery, payload: dict[str, Any]) -> dict[str, Any]:
        return {**payload, "event": cb}


class RetreatOutcomeFactory:
    """Convert retreat results into Telegram-friendly outcomes."""

    def __init__(self, translator: Translator) -> None:
        self._translate = translator

    def success(self) -> RetreatOutcome:
        return RetreatOutcome()

    def failure(self, note: str, cb: CallbackQuery) -> RetreatOutcome:
        tongue = self._tongue(cb)
        key = "barred" if note == "barred" else "missing"
        return RetreatOutcome(text=self._translate(key, tongue), show_alert=True)

    def render(self, result: RetreatResult, cb: CallbackQuery) -> RetreatOutcome:
        if result.success:
            return self.success()
        return self.failure(result.note or "generic", cb)

    @staticmethod
    def _tongue(obj: CallbackQuery) -> str:
        user = getattr(obj, "from_user", None)
        code = getattr(user, "language_code", None)
        return (code or "en").split("-")[0].lower()


@dataclass(frozen=True)
class RetreatResult:
    """Represents the outcome of a retreat workflow execution."""

    note: str | None = None

    @property
    def success(self) -> bool:
        return self.note is None

    @classmethod
    def ok(cls) -> "RetreatResult":
        return cls()

    @classmethod
    def failed(cls, note: str) -> "RetreatResult":
        return cls(note=note)


class RetreatWorkflow:
    """Drive navigator back actions while handling telemetry and context."""

    def __init__(
        self,
        *,
        telemetry: RetreatTelemetry,
        context: RetreatContextBuilder,
    ) -> None:
        self._telemetry = telemetry
        self._context = context

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatResult:
        scope = self._telemetry.scope(cb)
        self._telemetry.entered(scope)
        try:
            context = self._context.build(cb, payload)
            await navigator.back(context=context)
        except HistoryEmpty:
            return self._failure("history_empty", scope)
        except StateNotFound:
            return self._failure("state_not_found", scope)
        except InlineUnsupported:
            return self._failure("barred", scope)
        except Exception:  # pragma: no cover - defensive net for logging
            return self._failure("generic", scope)
        self._telemetry.completed(scope)
        return RetreatResult.ok()

    def _failure(self, note: str, scope: dict[str, object]) -> RetreatResult:
        self._telemetry.failed(note, scope)
        return RetreatResult.failed(note)


class RetreatHandler:
    """Adapt retreat workflow results to Telegram specific outcomes."""

    def __init__(
        self,
        telemetry: Telemetry,
        translator: Translator,
        *,
        workflow: RetreatWorkflow | None = None,
        instrumentation: RetreatTelemetry | None = None,
        context: RetreatContextBuilder | None = None,
        outcomes: RetreatOutcomeFactory | None = None,
    ) -> None:
        telemetry_tools = instrumentation or RetreatTelemetry(telemetry)
        context_builder = context or RetreatContextBuilder()
        self._workflow = workflow or RetreatWorkflow(
            telemetry=telemetry_tools,
            context=context_builder,
        )
        self._outcomes = outcomes or RetreatOutcomeFactory(translator)

    async def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatOutcome:
        result = await self._workflow.execute(cb, navigator, payload)
        return self._outcomes.render(result, cb)


__all__ = [
    "NavigatorBack",
    "RetreatHandler",
    "RetreatOutcome",
    "RetreatResult",
    "RetreatWorkflow",
]

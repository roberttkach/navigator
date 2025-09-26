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

    @staticmethod
    def _tongue(obj: CallbackQuery) -> str:
        user = getattr(obj, "from_user", None)
        code = getattr(user, "language_code", None)
        return (code or "en").split("-")[0].lower()


class RetreatHandler:
    """Coordinate navigator back operations with delegated collaborators."""

    def __init__(
        self,
        telemetry: Telemetry,
        translator: Translator,
        *,
        instrumentation: RetreatTelemetry | None = None,
        context: RetreatContextBuilder | None = None,
        outcomes: RetreatOutcomeFactory | None = None,
    ) -> None:
        self._telemetry = instrumentation or RetreatTelemetry(telemetry)
        self._context = context or RetreatContextBuilder()
        self._outcomes = outcomes or RetreatOutcomeFactory(translator)

    async def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatOutcome:
        scope = self._telemetry.scope(cb)
        self._telemetry.entered(scope)
        try:
            context = self._context.build(cb, payload)
            await navigator.back(context=context)
        except HistoryEmpty:
            return self._fail("history_empty", cb, scope)
        except StateNotFound:
            return self._fail("state_not_found", cb, scope)
        except InlineUnsupported:
            return self._fail("barred", cb, scope)
        except Exception:  # pragma: no cover - defensive net for logging
            return self._fail("generic", cb, scope)
        self._telemetry.completed(scope)
        return self._outcomes.success()

    def _fail(
        self,
        note: str,
        cb: CallbackQuery,
        scope: dict[str, object],
    ) -> RetreatOutcome:
        self._telemetry.failed(note, scope)
        return self._outcomes.failure(note, cb)


__all__ = ["NavigatorBack", "RetreatHandler", "RetreatOutcome"]

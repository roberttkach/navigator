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


class RetreatHandler:
    """Coordinate navigator back operations with telemetry and localization."""

    def __init__(self, telemetry: Telemetry, translator: Translator) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._translate = translator

    async def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, Any],
    ) -> RetreatOutcome:
        scope = {
            "chat": cb.message.chat.id if cb.message else 0,
            "inline": bool(cb.inline_message_id),
        }
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_ENTER,
            kind="callback",
            scope=scope,
        )
        try:
            context = {**payload, "event": cb}
            await navigator.back(context=context)
        except HistoryEmpty:
            return self._fail("history_empty", cb)
        except StateNotFound:
            return self._fail("state_not_found", cb)
        except InlineUnsupported:
            return self._fail("barred", cb)
        except Exception:  # pragma: no cover - defensive net for logging
            return self._fail("generic", cb)
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_DONE,
            kind="callback",
            scope=scope,
        )
        return RetreatOutcome()

    def _fail(self, note: str, cb: CallbackQuery) -> RetreatOutcome:
        self._channel.emit(
            logging.WARNING,
            LogCode.ROUTER_BACK_FAIL,
            kind="callback",
            note=note,
        )
        tongue = self._tongue(cb)
        key = "barred" if note == "barred" else "missing"
        return RetreatOutcome(text=self._translate(key, tongue), show_alert=True)

    @staticmethod
    def _tongue(obj: CallbackQuery) -> str:
        user = getattr(obj, "from_user", None)
        code = getattr(user, "language_code", None)
        return (code or "en").split("-")[0].lower()


__all__ = ["NavigatorBack", "RetreatHandler", "RetreatOutcome"]

from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from navigator.core.error import HistoryEmpty, InlineUnsupported, StateNotFound
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Any, Dict, Final, Protocol

from ..alerts import lexeme


class NavigatorLike(Protocol):
    async def back(self, context: Dict[str, Any]) -> None: ...


router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA: Final[str] = "back"


def instrument(telemetry: Telemetry, _container=None) -> None:
    """Attach a telemetry hub to the router runtime data."""

    router.data["telemetry"] = telemetry


def _channel() -> TelemetryChannel | None:
    telemetry = router.data.get("telemetry")
    if isinstance(telemetry, Telemetry):
        return telemetry.channel(__name__)
    return None


def _tongue(obj) -> str:
    u = getattr(obj, "from_user", None)
    code = getattr(u, "language_code", None)
    return (code or "en").split("-")[0].lower()


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def retreat(cb: CallbackQuery, navigator: NavigatorLike, **data: Dict[str, Any]) -> None:
    channel = _channel()
    try:
        if channel:
            channel.emit(
                logging.INFO,
                LogCode.ROUTER_BACK_ENTER,
                kind="callback",
                scope={
                    "chat": cb.message.chat.id if cb.message else 0,
                    "inline": bool(cb.inline_message_id),
                },
            )
        context = {**data, "event": cb}
        await navigator.back(context=context)
        if channel:
            channel.emit(
                logging.INFO,
                LogCode.ROUTER_BACK_DONE,
                kind="callback",
                scope={
                    "chat": cb.message.chat.id if cb.message else 0,
                    "inline": bool(cb.inline_message_id),
                },
            )
        await cb.answer()
    except HistoryEmpty:
        if channel:
            channel.emit(
                logging.WARNING,
                LogCode.ROUTER_BACK_FAIL,
                kind="callback",
                note="history_empty",
            )
        await cb.answer(lexeme("missing", _tongue(cb)), show_alert=True)
    except StateNotFound:
        if channel:
            channel.emit(
                logging.WARNING,
                LogCode.ROUTER_BACK_FAIL,
                kind="callback",
                note="state_not_found",
            )
        await cb.answer(lexeme("missing", _tongue(cb)), show_alert=True)
    except InlineUnsupported:
        if channel:
            channel.emit(
                logging.WARNING,
                LogCode.ROUTER_BACK_FAIL,
                kind="callback",
                note="barred",
            )
        await cb.answer(lexeme("barred", _tongue(cb)), show_alert=True)
    except Exception:
        if channel:
            channel.emit(
                logging.WARNING,
                LogCode.ROUTER_BACK_FAIL,
                kind="callback",
                note="generic",
            )
        await cb.answer(lexeme("missing", _tongue(cb)), show_alert=True)


__all__ = ["router", "NavigatorLike", "retreat", "BACK_CALLBACK_DATA"]

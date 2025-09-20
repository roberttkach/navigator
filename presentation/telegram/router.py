from __future__ import annotations

import logging
from typing import Any, Dict, Final

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from ..navigator import Navigator
from ...application.log.emit import jlog
from ...domain.error import HistoryEmpty, InlineUnsupported
from ...domain.value.lexicon import lexeme
from ...logging.code import LogCode

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA: Final[str] = "back"

logger = logging.getLogger(__name__)


def _lang_from(obj) -> str:
    u = getattr(obj, "from_user", None)
    code = getattr(u, "language_code", None)
    return (code or "en").split("-")[0].lower()


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def back_handler(cb: CallbackQuery, navigator: Navigator, **data: Dict[str, Any]) -> None:
    try:
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_ENTER, kind="callback",
             scope={"chat": cb.message.chat.id if cb.message else 0, "inline": bool(cb.inline_message_id)})
        handler_data = {**data, "event": cb}
        await navigator.back(handler_data=handler_data)
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_DONE, kind="callback",
             scope={"chat": cb.message.chat.id if cb.message else 0, "inline": bool(cb.inline_message_id)})
        await cb.answer()
    except HistoryEmpty:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="history_empty")
        await cb.answer(lexeme("prev_not_found", _lang_from(cb)), show_alert=True)
    except InlineUnsupported:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="inline_unsupported")
        await cb.answer(lexeme("inline_unsupported", _lang_from(cb)), show_alert=True)
    except Exception:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="generic")
        await cb.answer(lexeme("prev_not_found", _lang_from(cb)), show_alert=True)


BACK_TEXTS: Final = {lexeme("back", "ru"), lexeme("back", "en")}


@router.message(F.func(lambda m: getattr(m, "text", None) in BACK_TEXTS))
async def back_text_handler(msg: Message, navigator: Navigator, **data: Dict[str, Any]) -> None:
    try:
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_ENTER, kind="text",
             scope={"chat": msg.chat.id, "inline": False})
        handler_data = {**data, "event": msg}
        await navigator.back(handler_data=handler_data)
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_DONE, kind="text",
             scope={"chat": msg.chat.id, "inline": False})
    except HistoryEmpty:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="text", note="history_empty")
        await navigator.inform_history_is_empty()
    except Exception:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="text", note="generic")
        await navigator.inform_history_is_empty()

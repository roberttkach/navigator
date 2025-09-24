from __future__ import annotations

"""Aiogram router bindings for the Navigator facade."""

import logging
from typing import Any, Dict, Final, Protocol

from aiogram import F, Router
from aiogram.types import CallbackQuery

from navigator.domain.error import HistoryEmpty, InlineUnsupported, StateNotFound
from navigator.log import LogCode, jlog
from .lexicon import lexeme


class NavigatorLike(Protocol):
    async def back(self, context: Dict[str, Any]) -> None: ...

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA: Final[str] = "back"

logger = logging.getLogger(__name__)


def _tongue(obj) -> str:
    u = getattr(obj, "from_user", None)
    code = getattr(u, "language_code", None)
    return (code or "en").split("-")[0].lower()


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def retreat(cb: CallbackQuery, navigator: NavigatorLike, **data: Dict[str, Any]) -> None:
    try:
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_ENTER, kind="callback",
             scope={"chat": cb.message.chat.id if cb.message else 0, "inline": bool(cb.inline_message_id)})
        context = {**data, "event": cb}
        await navigator.back(context=context)
        jlog(logger, logging.INFO, LogCode.ROUTER_BACK_DONE, kind="callback",
             scope={"chat": cb.message.chat.id if cb.message else 0, "inline": bool(cb.inline_message_id)})
        await cb.answer()
    except HistoryEmpty:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="history_empty")
        await cb.answer(lexeme("prev_not_found", _tongue(cb)), show_alert=True)
    except StateNotFound:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="state_not_found")
        await cb.answer(lexeme("prev_not_found", _tongue(cb)), show_alert=True)
    except InlineUnsupported:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="inline_unsupported")
        await cb.answer(lexeme("inline_unsupported", _tongue(cb)), show_alert=True)
    except Exception:
        jlog(logger, logging.WARNING, LogCode.ROUTER_BACK_FAIL, kind="callback", note="generic")
        await cb.answer(lexeme("prev_not_found", _tongue(cb)), show_alert=True)



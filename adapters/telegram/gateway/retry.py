from __future__ import annotations

import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

from aiogram.exceptions import TelegramRetryAfter

from .patterns import NOT_MODIFIED, EDIT_FORBIDDEN
from ....domain.error import MessageNotChanged, MessageEditForbidden
from ....domain.log.emit import jlog
from ....domain.log.code import LogCode

T = TypeVar("T")
logger = logging.getLogger(__name__)


def _extract_retry_after(e: TelegramRetryAfter) -> int | None:
    val = getattr(e, "retry_after", None)
    if isinstance(val, int):
        return val
    params = getattr(e, "parameters", None)
    pa = getattr(params, "retry_after", None)
    if isinstance(pa, int):
        return pa
    return None


async def call_tg(fn: Callable[..., Awaitable[T]], *a, **kw) -> T:
    attempts = 0
    max_attempts = 6
    base = 1.5
    cap = 120.0
    max_total = 180.0
    waited = 0.0
    while True:
        try:
            return await fn(*a, **kw)
        except TelegramRetryAfter as e:
            ra = _extract_retry_after(e)
            if ra is not None:
                jlog(logger, logging.WARNING, LogCode.TELEGRAM_RETRY, retry_after=ra)
                sleep_for = float(ra)
            else:
                jlog(logger, logging.WARNING, LogCode.TELEGRAM_RETRY)
                sleep_for = min(cap, base ** attempts) + random.uniform(0.0, 0.5)
            if waited + sleep_for > max_total:
                raise
            if ra is None and attempts + 1 > max_attempts:
                raise
            await asyncio.sleep(sleep_for)
            waited += sleep_for
            attempts += 1
            continue
        except Exception as e:
            raw = getattr(e, "message", e)
            msg = str(raw)
            ml = msg.lower()
            if any(p in ml for p in NOT_MODIFIED):
                raise MessageNotChanged() from e
            if any(p in ml for p in EDIT_FORBIDDEN):
                raise MessageEditForbidden("gateway_edit_forbidden") from e
            raise

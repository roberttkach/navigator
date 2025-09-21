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


def _delay(error: TelegramRetryAfter) -> int | None:
    value = getattr(error, "retry_after", None)
    if isinstance(value, int):
        return value
    params = getattr(error, "parameters", None)
    param = getattr(params, "retry_after", None)
    if isinstance(param, int):
        return param
    return None


async def invoke(action: Callable[..., Awaitable[T]], *values, **labels) -> T:
    tries = 0
    quota = 6
    base = 1.5
    cap = 120.0
    timeout = 180.0
    waited = 0.0
    while True:
        try:
            return await action(*values, **labels)
        except TelegramRetryAfter as error:
            delay = _delay(error)
            if delay is not None:
                jlog(logger, logging.WARNING, LogCode.TELEGRAM_RETRY, retry=delay)
                pause = float(delay)
            else:
                jlog(logger, logging.WARNING, LogCode.TELEGRAM_RETRY)
                pause = min(cap, base ** tries) + random.uniform(0.0, 0.5)
            if waited + pause > timeout:
                raise
            if delay is None and tries + 1 > quota:
                raise
            await asyncio.sleep(pause)
            waited += pause
            tries += 1
            continue
        except Exception as error:
            raw = getattr(error, "message", error)
            message = str(raw)
            lower = message.lower()
            if any(p in lower for p in NOT_MODIFIED):
                raise MessageNotChanged() from error
            if any(p in lower for p in EDIT_FORBIDDEN):
                raise MessageEditForbidden("gateway_edit_forbidden") from error
            raise

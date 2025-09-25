from __future__ import annotations

import asyncio
import logging
import random
from aiogram.exceptions import TelegramRetryAfter
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from .patterns import EDIT_FORBIDDEN, NOT_MODIFIED
from ....core.error import EditForbidden, MessageUnchanged
from ....core.telemetry import LogCode, TelemetryChannel

P = ParamSpec("P")
T = TypeVar("T")


def _delay(error: TelegramRetryAfter) -> int | None:
    value = getattr(error, "retry_after", None)
    if isinstance(value, int):
        return value
    params = getattr(error, "parameters", None)
    param = getattr(params, "retry_after", None)
    if isinstance(param, int):
        return param
    return None


async def invoke(
        action: Callable[P, Awaitable[T]],
        *values: P.args,
        channel: TelemetryChannel,
        **labels: P.kwargs,
) -> T:
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
                channel.emit(logging.WARNING, LogCode.TELEGRAM_RETRY, retry=delay)
                pause = float(delay)
            else:
                channel.emit(logging.WARNING, LogCode.TELEGRAM_RETRY)
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
            if NOT_MODIFIED.matches(message):
                raise MessageUnchanged() from error
            if EDIT_FORBIDDEN.matches(message):
                raise EditForbidden("gateway_edit_forbidden") from error
            if "aiogram" in type(error).__module__:
                channel.emit(
                    logging.WARNING,
                    LogCode.TELEGRAM_UNHANDLED_ERROR,
                    description=message,
                    error_type=type(error).__name__,
                )
            raise

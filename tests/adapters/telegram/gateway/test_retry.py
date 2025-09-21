from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections.abc import Awaitable
from pathlib import Path
from typing import TypeVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from navigator.adapters.telegram.gateway.retry import invoke
from navigator.domain.error import MessageEditForbidden, MessageNotChanged
from navigator.domain.log.code import LogCode


class DummyTelegramError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


FakeAiogramError = type(
    "FakeAiogramError",
    (DummyTelegramError,),
    {"__module__": "aiogram.testing"},
)

T = TypeVar("T")


def run(coro: Awaitable[T]) -> T:  # noqa: UP047 - Python 3.11 runtime does not support PEP 695 syntax.
    return asyncio.run(coro)


def test_invoke_translates_not_modified() -> None:
    async def action() -> None:
        raise DummyTelegramError(
            "Bad Request: message is not modified: nothing to change",
        )

    with pytest.raises(MessageNotChanged):
        run(invoke(action))


def test_invoke_translates_edit_forbidden() -> None:
    async def action() -> None:
        raise DummyTelegramError(
            "Bad Request: message can be edited only within 48 hours",
        )

    with pytest.raises(MessageEditForbidden):
        run(invoke(action))


def test_invoke_logs_unhandled_aiogram_error(caplog: pytest.LogCaptureFixture) -> None:
    async def action() -> None:
        raise FakeAiogramError("Bad Request: some brand new message")

    caplog.set_level(logging.WARNING)

    with pytest.raises(FakeAiogramError):
        run(invoke(action))

    payloads = [json.loads(record.getMessage()) for record in caplog.records]
    assert any(
        payload.get("code") == LogCode.TELEGRAM_UNHANDLED_ERROR.value
        for payload in payloads
    )

"""Manual scenarios focused on gateway interactions."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import navigator.adapters.telegram.gateway.purge as purger
from navigator.adapters.telegram.errors import dismissible
from navigator.adapters.telegram.gateway import create_gateway
from navigator.adapters.telegram.gateway.purge import PurgeTask
from navigator.adapters.telegram.serializer.screen import SignatureScreen
from navigator.core.value.message import Scope

from .common import monitor
from navigator.presentation.alerts import missing


def wording() -> None:
    """Exercise Telegram gateway alert flow."""

    bot = SimpleNamespace(send_message=AsyncMock())

    class DummyCodec:
        def decode(self, markup):
            return markup

    class DummySchema:
        def send(self, *args, **kwargs):
            return {"text": {}, "caption": {}, "media": {}, "effect": None}

        def edit(self, *args, **kwargs):
            return {"text": {}, "caption": {}, "media": {}, "effect": None}

        def history(self, *args, **kwargs):  # pragma: no cover - not used
            return None

    class DummyLimits:
        def textlimit(self):
            return 4096

        def captionlimit(self):
            return 1024

        def groupmin(self):
            return 2

        def groupmax(self):
            return 10

        def groupmix(self):
            return set()

    class DummyPolicy:
        def admissible(self, path, *, inline):
            return True

        def adapt(self, path, *, native):
            return path

    telemetry = monitor()
    gateway = create_gateway(
        bot=bot,
        codec=DummyCodec(),
        limits=DummyLimits(),
        schema=DummySchema(),
        policy=DummyPolicy(),
        screen=SignatureScreen(telemetry=telemetry),
        chunk=10,
        truncate=False,
        deletepause=0.0,
        telemetry=telemetry,
    )
    scope = Scope(chat=42, lang="en")

    asyncio.run(gateway.alert(scope, "payload message"))

    bot.send_message.assert_awaited_once()
    call = bot.send_message.await_args
    assert call.args == ()
    assert call.kwargs["text"] == "payload message"
    assert call.kwargs["chat_id"] == scope.chat


def commerce() -> None:
    """Verify purge handles business message deletion."""

    scope = Scope(chat=11, lang="en", business="biz")
    bot = SimpleNamespace(
        delete_business_messages=AsyncMock(
            side_effect=[Exception("message to delete not found"), None]
        ),
        delete_messages=AsyncMock(),
    )
    runner = PurgeTask(bot=bot, chunk=2, delay=0.0, telemetry=monitor())

    captured = []

    async def capture(action, *args, **kwargs):
        captured.append((action, args, kwargs))
        return await action(*args, **kwargs)

    baseline = purger.invoke
    purger.invoke = capture
    try:
        asyncio.run(runner.execute(scope, [9, 1, 2]))
    finally:
        purger.invoke = baseline

    assert bot.delete_messages.await_count == 0
    assert bot.delete_business_messages.await_count == 2
    assert len(captured) == 2
    for action, args, kwargs in captured:
        assert action is bot.delete_business_messages
        assert not args
        assert kwargs["business_connection_id"] == scope.business
        assert kwargs["message_ids"]


def fragments() -> None:
    """List error fragments considered dismissible."""

    supported = (
        "error: message to delete not found in history",
        "oops, this message can't be deleted for everyone",
        "cannot delete the requested message right now",
        "message is too old to be removed",
        "warning: not enough rights to delete message",
        "already deleted or gone",
        "paid post cannot be removed",
        "item must not be deleted for 24 hours after creation",
    )

    for sample in supported:
        assert dismissible(sample)

    assert not dismissible("unexpected failure: try again later")


def translation() -> None:
    """Showcase localisation of missing alert."""

    scope = Scope(chat=0, lang="ru")
    payload = missing(scope)
    assert "Предыдущий экран" in payload


__all__ = ["commerce", "fragments", "translation", "wording"]

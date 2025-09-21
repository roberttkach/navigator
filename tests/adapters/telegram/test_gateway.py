import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.adapters.telegram.gateway.util import targets
from navigator.domain.value.message import Scope
from navigator.presentation.telegram.lexicon import lexeme


class DummyMarkupCodec:
    def encode(self, markup):  # pragma: no cover - simple stub
        return markup

    def decode(self, stored):  # pragma: no cover - simple stub
        return stored


def test_targets_includes_direct_messages_topic_id() -> None:
    scope = Scope(chat=42, direct_topic_id=777)

    kwargs = targets(scope)

    assert kwargs["chat_id"] == 42
    assert kwargs["direct_messages_topic_id"] == 777


def test_alert_forwards_direct_messages_topic_id() -> None:
    send_message = AsyncMock()
    bot = SimpleNamespace(send_message=send_message)
    gateway = TelegramGateway(bot=bot, markup_codec=DummyMarkupCodec())
    scope = Scope(chat=42, lang="en", direct_topic_id=777)

    asyncio.run(gateway.alert(scope))

    expected_text = lexeme("prev_not_found", "en")
    send_message.assert_awaited_once_with(
        text=expected_text,
        chat_id=42,
        direct_messages_topic_id=777,
    )

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.application.usecase.alarm import Alarm
from navigator.application.usecase.set import Setter
from navigator.domain.port.message import AlertPayload
from navigator.domain.value.message import Scope
from navigator.presentation.alerts import prev_not_found


def digest_alarm_uses_alert_provider() -> None:
    scope = Scope(chat=1, lang="en")
    payload = AlertPayload(text="alert text")
    provider = Mock(return_value=payload)
    gateway = Mock()
    gateway.alert = AsyncMock()

    alarm = Alarm(gateway=gateway, alert=provider)

    asyncio.run(alarm.execute(scope))

    provider.assert_called_once_with(scope)
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, payload)


def digest_setter_alerts_when_history_missing() -> None:
    scope = Scope(chat=5, lang="ru")
    payload = AlertPayload(text="нет данных")
    provider = Mock(return_value=payload)

    ledger = SimpleNamespace(recall=AsyncMock(return_value=[]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock())
    gateway = Mock()
    gateway.alert = AsyncMock()
    restorer = SimpleNamespace(revive=AsyncMock())
    orchestrator = SimpleNamespace(render=AsyncMock())
    latest = SimpleNamespace(mark=AsyncMock())

    setter = Setter(
        ledger=ledger,
        status=status,
        gateway=gateway,
        alert=provider,
        restorer=restorer,
        orchestrator=orchestrator,
        latest=latest,
    )

    asyncio.run(setter.execute(scope, goal="target", context={}))

    provider.assert_called_once_with(scope)
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, payload)
    ledger.archive.assert_not_awaited()
    orchestrator.render.assert_not_awaited()


def digest_telegram_gateway_uses_payload_text() -> None:
    bot = SimpleNamespace(send_message=AsyncMock())
    gateway = TelegramGateway(bot=bot, codec=object(), chunk=10, truncate=False)
    scope = Scope(chat=42, lang="en")
    payload = AlertPayload(text="payload message")

    asyncio.run(gateway.alert(scope, payload))

    bot.send_message.assert_awaited_once()
    call = bot.send_message.await_args
    assert call.args == ()
    assert call.kwargs["text"] == payload.text
    assert call.kwargs["chat_id"] == scope.chat


def extract_prev_not_found_localizes_scope_language() -> None:
    scope = Scope(chat=0, lang="ru")

    payload = prev_not_found(scope)

    assert "Предыдущий экран" in payload.text

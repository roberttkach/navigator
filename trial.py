import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.application.usecase.alarm import Alarm
from navigator.application.usecase.set import Setter
from navigator.domain.error import StateNotFound
from navigator.domain.value.message import Scope
from navigator.presentation.alerts import prev_not_found
from navigator.presentation.navigator import Navigator


def digest_alarm_uses_alert_provider() -> None:
    scope = Scope(chat=1, lang="en")
    provider = Mock(return_value="alert text")
    gateway = Mock()
    gateway.alert = AsyncMock()

    alarm = Alarm(gateway=gateway, alert=provider)

    asyncio.run(alarm.execute(scope))

    provider.assert_called_once_with(scope)
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "alert text")


def digest_alarm_prefers_explicit_text() -> None:
    scope = Scope(chat=1, lang="en")
    provider = Mock(return_value="fallback")
    gateway = Mock()
    gateway.alert = AsyncMock()

    alarm = Alarm(gateway=gateway, alert=provider)

    asyncio.run(alarm.execute(scope, text="override"))

    provider.assert_not_called()
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "override")


def digest_setter_raises_when_history_missing() -> None:
    scope = Scope(chat=5, lang="ru")
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
        restorer=restorer,
        orchestrator=orchestrator,
        latest=latest,
    )

    try:
        asyncio.run(setter.execute(scope, goal="target", context={}))
    except StateNotFound:
        pass
    else:
        raise AssertionError("StateNotFound was not raised")

    gateway.alert.assert_not_awaited()
    ledger.archive.assert_not_awaited()
    orchestrator.render.assert_not_awaited()


def digest_navigator_set_triggers_alarm_on_missing_state() -> None:
    scope = Scope(chat=10, lang="ru")
    setter = SimpleNamespace(execute=AsyncMock(side_effect=StateNotFound("missing")))
    alarm = SimpleNamespace(execute=AsyncMock())

    navigator = Navigator(
        appender=SimpleNamespace(),
        swapper=SimpleNamespace(),
        rewinder=SimpleNamespace(),
        setter=setter,
        trimmer=SimpleNamespace(),
        shifter=SimpleNamespace(),
        tailer=SimpleNamespace(peek=AsyncMock(), delete=AsyncMock(), edit=AsyncMock()),
        alarm=alarm,
        scope=scope,
    )

    asyncio.run(navigator.set("missing"))

    setter.execute.assert_awaited_once_with(scope, "missing", {})
    alarm.execute.assert_awaited_once()
    call = alarm.execute.await_args
    assert call.args == (scope,)
    assert call.kwargs == {"text": prev_not_found(scope)}


def digest_telegram_gateway_uses_provided_text() -> None:
    bot = SimpleNamespace(send_message=AsyncMock())
    gateway = TelegramGateway(bot=bot, codec=object(), chunk=10, truncate=False)
    scope = Scope(chat=42, lang="en")

    asyncio.run(gateway.alert(scope, "payload message"))

    bot.send_message.assert_awaited_once()
    call = bot.send_message.await_args
    assert call.args == ()
    assert call.kwargs["text"] == "payload message"
    assert call.kwargs["chat_id"] == scope.chat


def extract_prev_not_found_localizes_scope_language() -> None:
    scope = Scope(chat=0, lang="ru")

    payload = prev_not_found(scope)

    assert "Предыдущий экран" in payload

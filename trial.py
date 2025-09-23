import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from navigator.adapters.telegram.errors import dismissible
from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.adapters.telegram.gateway import delete as delete_module
from navigator.adapters.telegram.gateway.delete import DeleteBatch
from navigator.application.service.view.restorer import ViewRestorer
from navigator.application.usecase.alarm import Alarm
from navigator.application.usecase.set import Setter
from navigator.domain.entity.history import Entry
from navigator.domain.error import InlineUnsupported, StateNotFound
from navigator.domain.value.content import Payload
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


def digest_view_restorer_inline_dynamic_factory_rejects_multi_payload() -> None:
    async def forge():
        return [Payload(text="one"), Payload(text="two")]

    class Ledger:
        def __init__(self):
            self._mapping = {"dynamic": forge}

        def get(self, key: str):
            if key not in self._mapping:
                raise KeyError(key)
            return self._mapping[key]

    entry = Entry(state="alpha", view="dynamic", messages=[])
    restorer = ViewRestorer(ledger=Ledger())

    try:
        asyncio.run(restorer.revive(entry, {}, inline=True))
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def digest_view_restorer_dynamic_factory_allows_multi_payload_outside_inline() -> None:
    async def forge():
        return [Payload(text="one"), Payload(text="two")]

    class Ledger:
        def __init__(self):
            self._mapping = {"dynamic": forge}

        def get(self, key: str):
            if key not in self._mapping:
                raise KeyError(key)
            return self._mapping[key]

    entry = Entry(state="alpha", view="dynamic", messages=[])
    restorer = ViewRestorer(ledger=Ledger())

    restored = asyncio.run(restorer.revive(entry, {}, inline=False))

    assert [payload.text for payload in restored] == ["one", "two"]


def digest_setter_surfaces_inline_dynamic_factory_failure() -> None:
    scope = Scope(chat=5, lang="ru", inline="token")
    target = Entry(state="target", view="dynamic", messages=[])
    tail = Entry(state="tail", view=None, messages=[])
    ledger = SimpleNamespace(recall=AsyncMock(return_value=[target, tail]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock(return_value={}))
    gateway = Mock()
    gateway.alert = AsyncMock()
    restorer = SimpleNamespace(
        revive=AsyncMock(side_effect=InlineUnsupported("inline_dynamic_multi_payload"))
    )
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
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")

    orchestrator.render.assert_not_awaited()
    latest.mark.assert_not_awaited()


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


def digest_delete_batch_uses_business_api_only() -> None:
    scope = Scope(chat=11, lang="en", business="biz")
    bot = SimpleNamespace(
        delete_business_messages=AsyncMock(
            side_effect=[Exception("message to delete not found"), None]
        ),
        delete_messages=AsyncMock(),
    )
    runner = DeleteBatch(bot=bot, chunk=2)

    captured = []

    async def capture(action, *args, **kwargs):
        captured.append((action, args, kwargs))
        return await action(*args, **kwargs)

    original_invoke = delete_module.invoke
    delete_module.invoke = capture
    try:
        asyncio.run(runner.run(scope, [9, 1, 2]))
    finally:
        delete_module.invoke = original_invoke

    assert bot.delete_messages.await_count == 0
    assert bot.delete_business_messages.await_count == 2
    assert len(captured) == 2
    for action, args, kwargs in captured:
        assert action is bot.delete_business_messages
        assert not args
        assert kwargs["business_connection_id"] == scope.business
        assert kwargs["message_ids"]


def digest_telegram_errors_dismissible_recognizes_known_fragments() -> None:
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

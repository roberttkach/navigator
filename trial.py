import asyncio
import navigator.adapters.telegram.gateway.purge as purger
from contextlib import asynccontextmanager
from navigator.adapters.telegram.errors import dismissible
from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.adapters.telegram.gateway.purge import PurgeTask
from navigator.adapters.telegram.serializer.screen import SignatureScreen
from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.set import Setter
from navigator.core.entity.history import Entry
from navigator.core.entity.media import MediaItem, MediaType
from navigator.core.error import InlineUnsupported, StateNotFound
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.telemetry import Telemetry
from navigator.core.typing.result import TextMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope
from navigator.presentation.alerts import missing
from navigator.presentation.navigator import Navigator
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


class _StubTelemetryPort:
    def calibrate(self, mode: str) -> None:
        return None

    def emit(self, code, level, *, origin=None, **fields) -> None:
        return None


def monitor() -> Telemetry:
    return Telemetry(_StubTelemetryPort())


@asynccontextmanager
async def sentinel():
    yield


def reliance() -> None:
    scope = Scope(chat=1, lang="en")
    provider = Mock(return_value="alert text")
    gateway = Mock()
    gateway.alert = AsyncMock()

    alarm = Alarm(gateway=gateway, alert=provider, telemetry=monitor())

    asyncio.run(alarm.execute(scope))

    provider.assert_called_once_with(scope)
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "alert text")


def override() -> None:
    scope = Scope(chat=1, lang="en")
    provider = Mock(return_value="fallback")
    gateway = Mock()
    gateway.alert = AsyncMock()

    alarm = Alarm(gateway=gateway, alert=provider, telemetry=monitor())

    asyncio.run(alarm.execute(scope, text="override"))

    provider.assert_not_called()
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "override")


def absence() -> None:
    scope = Scope(chat=5, lang="ru")
    ledger = SimpleNamespace(recall=AsyncMock(return_value=[]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock())
    gateway = Mock()
    gateway.alert = AsyncMock()
    restorer = SimpleNamespace(revive=AsyncMock())
    planner = SimpleNamespace(render=AsyncMock())
    latest = SimpleNamespace(mark=AsyncMock())

    setter = Setter(
        ledger=ledger,
        status=status,
        gateway=gateway,
        restorer=restorer,
        planner=planner,
        latest=latest,
        telemetry=monitor(),
    )

    try:
        asyncio.run(setter.execute(scope, goal="target", context={}))
    except StateNotFound:
        pass
    else:
        raise AssertionError("StateNotFound was not raised")

    gateway.alert.assert_not_awaited()
    ledger.archive.assert_not_awaited()
    planner.render.assert_not_awaited()


def veto() -> None:
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
    restorer = ViewRestorer(ledger=Ledger(), telemetry=monitor())

    try:
        asyncio.run(restorer.revive(entry, {}, inline=True))
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def assent() -> None:
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
    restorer = ViewRestorer(ledger=Ledger(), telemetry=monitor())

    restored = asyncio.run(restorer.revive(entry, {}, inline=False))

    assert [payload.text for payload in restored] == ["one", "two"]


def surface() -> None:
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
    planner = SimpleNamespace(render=AsyncMock())
    latest = SimpleNamespace(mark=AsyncMock())

    setter = Setter(
        ledger=ledger,
        status=status,
        gateway=gateway,
        restorer=restorer,
        planner=planner,
        latest=latest,
        telemetry=monitor(),
    )

    try:
        asyncio.run(setter.execute(scope, goal="target", context={}))
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")

    planner.render.assert_not_awaited()
    latest.mark.assert_not_awaited()


def rebuff() -> None:
    scope = Scope(chat=7, lang="en", inline="token")
    planner = ViewPlanner(
        executor=SimpleNamespace(),
        inline=SimpleNamespace(handle=AsyncMock()),
        album=SimpleNamespace(refresh=AsyncMock()),
        rendering=RenderingConfig(),
        telemetry=monitor(),
    )

    try:
        asyncio.run(
            planner.render(
                scope,
                [Payload(text="one"), Payload(text="two")],
                trail=None,
                inline=True,
            )
        )
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support multi-message nodes"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def refuse() -> None:
    scope = Scope(chat=8, lang="en", inline="token")
    planner = ViewPlanner(
        executor=SimpleNamespace(),
        inline=SimpleNamespace(handle=AsyncMock()),
        album=SimpleNamespace(refresh=AsyncMock()),
        rendering=RenderingConfig(),
        telemetry=monitor(),
    )
    album = [
        MediaItem(type=MediaType.PHOTO, path="file-a", caption="a"),
        MediaItem(type=MediaType.PHOTO, path="file-b", caption="b"),
    ]

    try:
        asyncio.run(
            planner.render(
                scope,
                [Payload(group=album)],
                trail=None,
                inline=True,
            )
        )
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support media groups"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def decline() -> None:
    scope = Scope(chat=9, lang="en", inline="token")
    latest = SimpleNamespace(peek=AsyncMock(return_value=100), mark=AsyncMock())
    ledger = SimpleNamespace(recall=AsyncMock(), archive=AsyncMock())
    planner = SimpleNamespace(render=AsyncMock())
    executor = SimpleNamespace(
        delete=AsyncMock(),
        execute=AsyncMock(),
        refine=Mock(return_value=TextMeta(text="noop", inline=True)),
    )
    inline = SimpleNamespace(handle=AsyncMock())
    tailer = Tailer(
        latest=latest,
        ledger=ledger,
        planner=planner,
        executor=executor,
        inline=inline,
        rendering=RenderingConfig(),
        telemetry=monitor(),
    )
    payload = Payload(
        group=[
            MediaItem(type=MediaType.PHOTO, path="file-x"),
            MediaItem(type=MediaType.PHOTO, path="file-y"),
        ]
    )

    try:
        asyncio.run(tailer.edit(scope, payload))
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support media groups"
    else:
        raise AssertionError("InlineUnsupported was not raised")

    ledger.recall.assert_not_awaited()


def siren() -> None:
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
        guard=lambda _: sentinel(),
        telemetry=monitor(),
    )

    asyncio.run(navigator.set("missing"))

    setter.execute.assert_awaited_once_with(scope, "missing", {})
    alarm.execute.assert_awaited_once()
    call = alarm.execute.await_args
    assert call.args == (scope,)
    assert call.kwargs == {"text": missing(scope)}


def wording() -> None:
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
    gateway = TelegramGateway(
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


def translation() -> None:
    scope = Scope(chat=0, lang="ru")

    payload = missing(scope)

    assert "Предыдущий экран" in payload


def commerce() -> None:
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

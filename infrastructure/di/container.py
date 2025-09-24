from __future__ import annotations

from dependency_injector import containers, providers
from aiogram.fsm.context import FSMContext

from ...adapters.storage.chronicle import Chronicle
from ...adapters.storage.latest import Latest
from ...adapters.storage.status import Status
from ...adapters.telegram.gateway import TelegramGateway
from ...adapters.telegram.codec import AiogramCodec
from ...adapters.telegram.media import TelegramMediaPolicy
from ...adapters.telegram.serializer import (
    SignatureScreen,
    TelegramExtraSchema,
    TelegramLinkPreviewCodec,
)
from ...application.locks.guard import GuardFactory
from ...application.map.entry import EntryMapper
from ...application.service.view.album import AlbumService
from ...application.service.view.executor import EditExecutor
from ...application.service.view.inline import InlineStrategy
from ...application.service.view.planner import ViewPlanner
from ...application.service.view.restorer import ViewRestorer
from ...application.usecase.add import Appender
from ...application.usecase.back import Rewinder
from ...application.usecase.last import Tailer
from ...application.usecase.alarm import Alarm
from ...application.usecase.pop import Trimmer
from ...application.usecase.rebase import Shifter
from ...application.usecase.replace import Swapper
from ...application.usecase.set import Setter
from ...domain.port.factory import ViewLedger
from ...domain.service.rendering.config import RenderingConfig
from ..clock.system import SystemClock
from ..config.settings import load as load_settings
from ..limits.config import ConfigLimits
from ..locks.memory import MemoryLockProvider


class AppContainer(containers.DeclarativeContainer):
    settings = providers.Singleton(load_settings)

    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()

    codec = providers.Singleton(AiogramCodec)
    clock = providers.Singleton(SystemClock)
    limits = providers.Singleton(
        ConfigLimits,
        text=settings.provided.text_limit,
        caption=settings.provided.caption_limit,
        floor=settings.provided.album_floor,
        ceiling=settings.provided.album_ceiling,
        blend=settings.provided.album_blend_set,
    )
    screen = providers.Factory(SignatureScreen)
    schema = providers.Factory(TelegramExtraSchema)
    preview = providers.Factory(TelegramLinkPreviewCodec)
    policy = providers.Factory(TelegramMediaPolicy, strict=settings.provided.strictpath)
    lock_provider = providers.Singleton(MemoryLockProvider)
    guard = providers.Factory(GuardFactory, provider=lock_provider)

    rendering = providers.Factory(RenderingConfig, thumbguard=settings.provided.thumbguard)

    chronicle = providers.Factory(Chronicle, state=state)
    status = providers.Factory(Status, state=state)
    latest = providers.Factory(Latest, state=state)
    mapper = providers.Factory(EntryMapper, ledger=ledger)
    gateway = providers.Factory(
        TelegramGateway,
        bot=event.provided.bot,
        codec=codec,
        limits=limits,
        schema=schema,
        policy=policy,
        screen=screen,
        preview=preview,
        chunk=settings.provided.chunk,
        truncate=settings.provided.truncate,
        delete_delay=settings.provided.delete_delay,
    )

    inline = providers.Factory(InlineStrategy, policy=policy)
    executor = providers.Factory(EditExecutor, gateway=gateway)
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=limits,
        thumbguard=settings.provided.thumbguard,
    )
    planner = providers.Factory(
        ViewPlanner,
        executor=executor,
        inline=inline,
        album=album,
        rendering=rendering,
    )
    restorer = providers.Factory(ViewRestorer, ledger=ledger)

    appender = providers.Factory(
        Appender,
        archive=chronicle,
        state=status,
        tail=latest,
        planner=planner,
        mapper=mapper,
        limit=settings.provided.history_limit,
    )
    swapper = providers.Factory(
        Swapper,
        archive=chronicle,
        state=status,
        tail=latest,
        planner=planner,
        mapper=mapper,
        limit=settings.provided.history_limit,
    )
    rewinder = providers.Factory(
        Rewinder,
        ledger=chronicle,
        status=status,
        gateway=gateway,
        restorer=restorer,
        planner=planner,
        latest=latest,
    )
    setter = providers.Factory(
        Setter,
        ledger=chronicle,
        status=status,
        gateway=gateway,
        restorer=restorer,
        planner=planner,
        latest=latest,
    )
    trimmer = providers.Factory(Trimmer, ledger=chronicle, latest=latest)
    shifter = providers.Factory(Shifter, ledger=chronicle, latest=latest)
    tailer = providers.Factory(
        Tailer,
        latest=latest,
        ledger=chronicle,
        planner=planner,
        executor=executor,
        inline=inline,
        rendering=rendering,
    )
    alarm = providers.Factory(
        Alarm,
        gateway=gateway,
        alert=alert,
    )


__all__ = ["AppContainer"]

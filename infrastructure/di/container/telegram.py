from __future__ import annotations

from dependency_injector import containers, providers

from ...adapters.telegram.codec import AiogramCodec
from ...adapters.telegram.gateway import TelegramGateway
from ...adapters.telegram.media import TelegramMediaPolicy
from ...adapters.telegram.serializer import (
    SignatureScreen,
    TelegramExtraSchema,
    TelegramLinkPreviewCodec,
)
from ...application.service.view.album import AlbumService
from ...application.service.view.executor import EditExecutor
from ...application.service.view.inline import InlineStrategy


class TelegramContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()

    codec = providers.Singleton(AiogramCodec)
    schema = providers.Factory(TelegramExtraSchema)
    preview = providers.Factory(TelegramLinkPreviewCodec)
    policy = providers.Factory(TelegramMediaPolicy, strict=core.settings.provided.strictpath)
    screen = providers.Factory(SignatureScreen)
    gateway = providers.Factory(
        TelegramGateway,
        bot=core.event.provided.bot,
        codec=codec,
        limits=core.limits,
        schema=schema,
        policy=policy,
        screen=screen,
        preview=preview,
        chunk=core.settings.provided.chunk,
        truncate=core.settings.provided.truncate,
        delete_delay=core.settings.provided.delete_delay,
    )
    inline = providers.Factory(InlineStrategy, policy=policy)
    executor = providers.Factory(EditExecutor, gateway=gateway)
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=core.limits,
        thumbguard=core.settings.provided.thumbguard,
    )


__all__ = ["TelegramContainer"]

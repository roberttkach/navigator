from dependency_injector import containers, providers

from navigator.adapters.telegram.codec import AiogramCodec
from navigator.adapters.telegram.gateway import TelegramGateway
from navigator.adapters.telegram.media import TelegramMediaPolicy
from navigator.adapters.telegram.serializer import (
    SignatureScreen,
    TelegramExtraSchema,
    TelegramLinkPreviewCodec,
)
from navigator.app.service.view.album import AlbumService
from navigator.app.service.view.executor import EditExecutor
from navigator.app.service.view.inline import InlineHandler, InlineEditor, InlineGuard, InlineRemapper


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
    inline_guard = providers.Factory(InlineGuard, policy=policy)
    inline_remapper = providers.Factory(InlineRemapper)
    inline_editor = providers.Factory(InlineEditor)
    inline = providers.Factory(
        InlineHandler,
        guard=inline_guard,
        remapper=inline_remapper,
        editor=inline_editor,
    )
    executor = providers.Factory(EditExecutor, gateway=gateway)
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=core.limits,
        thumbguard=core.settings.provided.thumbguard,
    )


__all__ = ["TelegramContainer"]

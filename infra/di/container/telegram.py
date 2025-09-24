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
from navigator.core.telemetry import Telemetry


class TelegramContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    codec = providers.Singleton(AiogramCodec, telemetry=telemetry)
    schema = providers.Factory(TelegramExtraSchema)
    preview = providers.Factory(TelegramLinkPreviewCodec)
    policy = providers.Factory(TelegramMediaPolicy, strict=core.settings.provided.strictpath)
    screen = providers.Factory(SignatureScreen, telemetry=telemetry)
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
        deletepause=core.settings.provided.deletepause,
        telemetry=telemetry,
    )
    inline_guard = providers.Factory(InlineGuard, policy=policy)
    inline_remapper = providers.Factory(InlineRemapper)
    inline_editor = providers.Factory(InlineEditor)
    inline = providers.Factory(
        InlineHandler,
        guard=inline_guard,
        remapper=inline_remapper,
        editor=inline_editor,
        telemetry=telemetry,
    )
    executor = providers.Factory(EditExecutor, gateway=gateway, telemetry=telemetry)
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=core.limits,
        thumbguard=core.settings.provided.thumbguard,
        telemetry=telemetry,
    )


__all__ = ["TelegramContainer"]

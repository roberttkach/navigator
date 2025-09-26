from dependency_injector import containers, providers

from navigator.adapters.telegram.codec import AiogramCodec
from navigator.adapters.telegram.gateway import create_gateway
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
        create_gateway,
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
    sentinel = providers.Factory(InlineGuard, policy=policy)
    mapper = providers.Factory(InlineRemapper)
    scribe = providers.Factory(InlineEditor)
    inline = providers.Factory(
        InlineHandler,
        guard=sentinel,
        remapper=mapper,
        editor=scribe,
        telemetry=telemetry,
    )
    executor = providers.Factory(EditExecutor.create, gateway=gateway, telemetry=telemetry)
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=core.limits,
        thumbguard=core.settings.provided.thumbguard,
        telemetry=telemetry,
    )


__all__ = ["TelegramContainer"]

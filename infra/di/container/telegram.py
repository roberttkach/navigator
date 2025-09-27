"""Telegram specific composition of infrastructure and view services."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.adapters.telegram.codec import AiogramCodec
from navigator.adapters.telegram.entities import TELEGRAM_ENTITY_SANITIZER
from navigator.adapters.telegram.gateway import create_gateway
from navigator.adapters.telegram.media import TelegramMediaPolicy
from navigator.adapters.telegram.serializer import (
    SignatureScreen,
    TelegramExtraSchema,
    TelegramLinkPreviewCodec,
)
from navigator.app.service.view.album import AlbumService
from navigator.app.service.view.executor import create_edit_executor
from navigator.app.service.view.inline import InlineHandler, InlineEditor, InlineGuard, InlineRemapper
from navigator.core.telemetry import Telemetry


class TelegramInfrastructureContainer(containers.DeclarativeContainer):
    """Assemble Telegram specific gateway and codec dependencies."""

    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    codec = providers.Singleton(AiogramCodec, telemetry=telemetry)
    schema = providers.Factory(TelegramExtraSchema)
    preview = providers.Factory(TelegramLinkPreviewCodec)
    policy = providers.Factory(TelegramMediaPolicy, strict=core.settings.provided.strictpath)
    entities = providers.Object(TELEGRAM_ENTITY_SANITIZER)
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


class TelegramViewServicesContainer(containers.DeclarativeContainer):
    """Build view level helpers on top of Telegram infrastructure."""

    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    infrastructure = providers.DependenciesContainer()

    sentinel = providers.Factory(InlineGuard, policy=infrastructure.policy)
    mapper = providers.Factory(InlineRemapper)
    scribe = providers.Factory(InlineEditor)
    inline = providers.Factory(
        InlineHandler,
        guard=sentinel,
        remapper=mapper,
        editor=scribe,
        telemetry=telemetry,
    )
    executor = providers.Factory(
        create_edit_executor,
        gateway=infrastructure.gateway,
        telemetry=telemetry,
    )
    album = providers.Factory(
        AlbumService,
        executor=executor,
        limits=core.limits,
        thumbguard=core.settings.provided.thumbguard,
        telemetry=telemetry,
    )


class TelegramContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    infrastructure = providers.Container(
        TelegramInfrastructureContainer,
        core=core,
        telemetry=telemetry,
    )
    view_services = providers.Container(
        TelegramViewServicesContainer,
        core=core,
        telemetry=telemetry,
        infrastructure=infrastructure,
    )

    codec = infrastructure.provided.codec
    schema = infrastructure.provided.schema
    preview = infrastructure.provided.preview
    policy = infrastructure.provided.policy
    entities = infrastructure.provided.entities
    screen = infrastructure.provided.screen
    gateway = infrastructure.provided.gateway
    sentinel = view_services.provided.sentinel
    mapper = view_services.provided.mapper
    scribe = view_services.provided.scribe
    inline = view_services.provided.inline
    executor = view_services.provided.executor
    album = view_services.provided.album


__all__ = ["TelegramContainer"]

from __future__ import annotations

from aiogram.fsm.context import FSMContext
from dependency_injector import containers, providers

from navigator.app.locks.guard import GuardFactory
from navigator.core.port.factory import ViewLedger
from navigator.core.service.rendering.config import RenderingConfig
from navigator.infra.clock.system import SystemClock
from navigator.infra.config.settings import load as load_settings
from navigator.infra.limits.config import ConfigLimits
from navigator.infra.locks.memory import MemoryLockProvider


class CoreContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()

    settings = providers.Singleton(load_settings)
    clock = providers.Singleton(SystemClock)
    limits = providers.Singleton(
        ConfigLimits,
        text=settings.provided.text_limit,
        caption=settings.provided.caption_limit,
        floor=settings.provided.album_floor,
        ceiling=settings.provided.album_ceiling,
        blend=settings.provided.album_blend_set,
    )
    lock_provider = providers.Singleton(MemoryLockProvider)
    guard = providers.Factory(GuardFactory, provider=lock_provider)
    rendering = providers.Factory(RenderingConfig, thumbguard=settings.provided.thumbguard)


__all__ = ["CoreContainer"]

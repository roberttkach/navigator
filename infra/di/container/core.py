from __future__ import annotations

from aiogram.fsm.context import FSMContext
from dependency_injector import containers, providers

from navigator.app.locks.guard import GuardFactory
from navigator.core.port.factory import ViewLedger
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.telemetry import Telemetry
from navigator.infra.clock.system import SystemClock
from navigator.infra.config.settings import load as ingest
from navigator.infra.limits.config import ConfigLimits
from navigator.infra.locks.memory import MemoryLatch


class CoreContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()
    telemetry = providers.Dependency(instance_of=Telemetry)

    settings = providers.Singleton(ingest)
    clock = providers.Singleton(SystemClock)
    limits = providers.Singleton(
        ConfigLimits,
        text=settings.provided.textlimit,
        caption=settings.provided.captionlimit,
        minimum=settings.provided.groupmin,
        maximum=settings.provided.groupmax,
        mix=settings.provided.mixset,
    )
    locker = providers.Singleton(MemoryLatch)
    guard = providers.Factory(GuardFactory, provider=locker)
    rendering = providers.Factory(RenderingConfig, thumbguard=settings.provided.thumbguard)


__all__ = ["CoreContainer"]

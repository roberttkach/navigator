"""Assemblers bridging Telegram events with navigator runtime."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.app.service.navigator_runtime import (
    NavigatorRuntimeProvider,
    RuntimeAssemblyConfiguration,
    assemble_navigator,
    default_configuration,
)
from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.presentation.navigator import Navigator

from .alerts import missing
from .instrumentation import instrument_for_router
from .router import router as default_router
from .scope import outline


class NavigatorAssembler(Protocol):
    """Protocol describing navigator assembly for presentation layer."""

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator: ...


@dataclass(frozen=True)
class TelegramRuntimeConfiguration:
    """Configuration bundle describing runtime assembly policies."""

    instrumentation: Sequence[NavigatorRuntimeInstrument]
    missing_alert: MissingAlert

    @classmethod
    def create(
        cls,
        *,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> "TelegramRuntimeConfiguration":
        instruments: Sequence[NavigatorRuntimeInstrument]
        if instrumentation is None:
            instruments = (instrument_for_router(default_router),)
        else:
            instruments = tuple(instrumentation)
        return cls(instrumentation=instruments, missing_alert=missing_alert or missing)

    def as_configuration(self, overrides: NavigatorAssemblyOverrides | None) -> RuntimeAssemblyConfiguration[Navigator]:
        """Translate Telegram configuration into a runtime configuration."""

        return default_configuration(
            instrumentation=tuple(self.instrumentation),
            missing_alert=self.missing_alert,
            overrides=overrides,
            facade_type=Navigator,
        )


@dataclass(frozen=True)
class TelegramNavigatorAssembler:
    """Concrete assembler translating Telegram primitives for navigator runtime."""

    def __init__(
        self,
        ledger: ViewLedger,
        *,
        configuration: TelegramRuntimeConfiguration | None = None,
        overrides: NavigatorAssemblyOverrides | None = None,
        provider: NavigatorRuntimeProvider[Navigator] | None = None,
    ) -> None:
        self._ledger = ledger
        self._configuration = configuration or TelegramRuntimeConfiguration.create()
        self._provider = provider or NavigatorRuntimeProvider(
            assemble_navigator,
            configuration=self._configuration.as_configuration(overrides),
        )

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator:
        navigator = await self._provider.assemble(
            event=event,
            state=state,
            ledger=self._ledger,
            scope=outline(event),
        )
        return cast(Navigator, navigator)


NavigatorInstrument = NavigatorRuntimeInstrument


__all__ = [
    "NavigatorAssembler",
    "NavigatorInstrument",
    "TelegramNavigatorAssembler",
    "TelegramRuntimeConfiguration",
]

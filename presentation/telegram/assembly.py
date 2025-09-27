"""Assemblers bridging Telegram events with navigator runtime."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol, cast

from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.app.service.navigator_runtime import NavigatorRuntimeProvider
from navigator.contracts.runtime import NavigatorAssemblyOverrides, NavigatorRuntimeInstrument
from navigator.core.port.factory import ViewLedger
from navigator.presentation.navigator import Navigator

from .runtime_provider import (
    AssemblyProvider,
    RuntimeEntrypoint,
    RuntimeResolver,
    TelegramRuntimeConfiguration,
    TelegramRuntimeBuilder,
    create_runtime_builder,
)
from .scope import outline


class NavigatorAssembler(Protocol):
    """Protocol describing navigator assembly for presentation layer."""

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator: ...


@dataclass(frozen=True)
class TelegramNavigatorAssembler:
    """Concrete assembler translating Telegram primitives for navigator runtime."""

    _ledger: ViewLedger
    _provider: NavigatorRuntimeProvider[Navigator]

    @classmethod
    def create(
        cls,
        ledger: ViewLedger,
        *,
        configuration: TelegramRuntimeConfiguration | None = None,
        overrides: NavigatorAssemblyOverrides | None = None,
        provider: NavigatorRuntimeProvider[Navigator] | None = None,
        runtime_resolver: RuntimeResolver | None = None,
        instrumentation_factory: Callable[[], Iterable[NavigatorRuntimeInstrument]] | None = None,
        assembly_provider: AssemblyProvider | None = None,
        entrypoint: RuntimeEntrypoint | None = None,
    ) -> "TelegramNavigatorAssembler":
        builder = create_runtime_builder(
            instrumentation_factory=instrumentation_factory,
            runtime_resolver=runtime_resolver,
            assembly_provider=assembly_provider,
            entrypoint=entrypoint,
        )
        runtime_provider = builder.build_provider(
            base_configuration=configuration,
            overrides=overrides,
            provider=provider,
            facade_type=Navigator,
        )
        return cls(ledger=ledger, provider=runtime_provider)

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
    "TelegramRuntimeBuilder",
]

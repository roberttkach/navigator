"""Assemblers bridging Telegram events with navigator runtime."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.api import assemble as assemble_navigator
from navigator.api.contracts import NavigatorRuntimeInstrument
from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.presentation.navigator import Navigator

from .alerts import missing
from .instrumentation import instrument as default_instrument
from .scope import outline


class NavigatorAssembler(Protocol):
    """Protocol describing navigator assembly for presentation layer."""

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator: ...


class TelegramNavigatorAssembler:
    """Concrete assembler translating Telegram primitives for navigator API."""

    def __init__(
        self,
        ledger: ViewLedger,
        *,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> None:
        self._ledger = ledger
        self._instrumentation: Sequence[NavigatorRuntimeInstrument] | None = (
            tuple(instrumentation) if instrumentation is not None else None
        )
        self._missing_alert = missing_alert or missing

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator:
        instrumentation = self._instrumentation or (default_instrument,)
        navigator = await assemble_navigator(
            event=event,
            state=state,
            ledger=self._ledger,
            scope=outline(event),
            instrumentation=instrumentation,
            missing_alert=self._missing_alert,
        )
        return navigator


NavigatorInstrument = NavigatorRuntimeInstrument


__all__ = ["NavigatorAssembler", "NavigatorInstrument", "TelegramNavigatorAssembler"]

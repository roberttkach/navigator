"""Assemblers bridging Telegram events with navigator runtime."""
from __future__ import annotations

from typing import Protocol

from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.api import assemble as assemble_navigator
from navigator.core.port.factory import ViewLedger
from navigator.presentation.navigator import Navigator

from .alerts import missing
from .instrumentation import build_retreat_instrument
from .router import retreat_configurator, router
from .scope import outline


class NavigatorAssembler(Protocol):
    """Protocol describing navigator assembly for presentation layer."""

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator: ...


class TelegramNavigatorAssembler:
    """Concrete assembler translating Telegram primitives for navigator API."""

    def __init__(self, ledger: ViewLedger) -> None:
        self._ledger = ledger
        self._instrumentation = (
            build_retreat_instrument(retreat_configurator(router)),
        )

    async def assemble(self, event: TelegramObject, state: FSMContext) -> Navigator:
        navigator = await assemble_navigator(
            event=event,
            state=state,
            ledger=self._ledger,
            scope=outline(event),
            instrumentation=self._instrumentation,
            missing_alert=missing,
        )
        return navigator


__all__ = ["NavigatorAssembler", "TelegramNavigatorAssembler"]

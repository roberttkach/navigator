"""Aiogram middleware that injects a Navigator instance into handler context."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.bootstrap.navigator import NavigatorAssembler as BootstrapNavigatorAssembler
from navigator.core.port.factory import ViewLedger

from .assembly import NavigatorAssembler, TelegramNavigatorAssembler

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


class NavigatorMiddleware(BaseMiddleware):
    """Construct and attach Navigator facades for every incoming event."""

    def __init__(self, assembler: NavigatorAssembler) -> None:
        self._assembler = assembler

    @classmethod
    def from_ledger(
        cls,
        ledger: ViewLedger,
        *,
        instrumentation: Iterable[BootstrapNavigatorAssembler.Instrument] | None = None,
    ) -> "NavigatorMiddleware":
        """Provide a convenient constructor for the default assembler."""

        return cls(
            TelegramNavigatorAssembler(ledger, instrumentation=instrumentation)
        )

    async def __call__(
            self,
            handler: Handler,
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if not isinstance(state, FSMContext):  # pragma: no cover - runtime guard
            raise RuntimeError("FSMContext instance is required to assemble Navigator")
        navigator = await self._assembler.assemble(event, state)
        data["navigator"] = navigator
        return await handler(event, data)


__all__ = ["NavigatorMiddleware", "Handler"]

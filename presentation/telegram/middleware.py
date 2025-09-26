"""Aiogram middleware that injects a Navigator instance into handler context."""
from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict

from navigator.core.port.factory import ViewLedger

from .assembly import NavigatorAssembler, TelegramNavigatorAssembler

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


class NavigatorMiddleware(BaseMiddleware):
    """Construct and attach Navigator facades for every incoming event."""

    def __init__(self, assembler: NavigatorAssembler) -> None:
        self._assembler = assembler

    @classmethod
    def from_ledger(cls, ledger: ViewLedger) -> "NavigatorMiddleware":
        """Provide a convenient constructor for the default assembler."""

        return cls(TelegramNavigatorAssembler(ledger))

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

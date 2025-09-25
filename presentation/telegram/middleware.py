"""Aiogram middleware that injects a Navigator instance into handler context."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from navigator.api import assemble as assemble_navigator
from navigator.core.port.factory import ViewLedger
from .scope import outline

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


class NavigatorMiddleware(BaseMiddleware):
    """Construct and attach Navigator facades for every incoming event."""

    def __init__(self, ledger: ViewLedger) -> None:
        self._ledger = ledger

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if not isinstance(state, FSMContext):  # pragma: no cover - runtime guard
            raise RuntimeError("FSMContext instance is required to assemble Navigator")
        navigator = await assemble_navigator(
            event=event,
            state=state,
            ledger=self._ledger,
            scope=outline(event),
        )
        data["navigator"] = navigator
        return await handler(event, data)


__all__ = ["NavigatorMiddleware", "Handler"]


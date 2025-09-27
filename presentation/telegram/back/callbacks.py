"""Telegram specific callback adapters for retreat handlers."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from aiogram.types import CallbackQuery

from .handler import RetreatHandler
from .outcome import RetreatOutcome
from .protocols import NavigatorBack


class RetreatCallback(Protocol):
    """Protocol describing Telegram callback signatures."""

    def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        **data: dict[str, Any],
    ) -> Awaitable[None]: ...


def adapt_retreat_handler(handler: RetreatHandler) -> RetreatCallback:
    """Wrap a retreat handler into an Aiogram callback."""

    async def _callback(
        cb: CallbackQuery,
        navigator: NavigatorBack,
        **data: dict[str, Any],
    ) -> None:
        outcome: RetreatOutcome = await handler(cb, navigator, data)
        await cb.answer(outcome.text, show_alert=outcome.show_alert)

    return _callback


def build_callback(factory: Callable[[], RetreatHandler]) -> RetreatCallback:
    """Create a callback by instantiating a handler lazily."""

    handler = factory()
    return adapt_retreat_handler(handler)


__all__ = ["RetreatCallback", "adapt_retreat_handler", "build_callback"]

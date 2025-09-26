from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery

from navigator.core.telemetry import Telemetry
from navigator.presentation.alerts import lexeme
from navigator.presentation.telegram.back import (
    NavigatorBack,
    Translator,
    RetreatHandler,
    RetreatOutcome,
)

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA = "back"


@dataclass(frozen=True)
class RetreatDependencies:
    """Dependencies required to configure retreat handling."""

    telemetry: Telemetry
    translator: Translator = lexeme


class RetreatHandlerProvider:
    """Manage retreat handler lifecycle without mutating router globals."""

    def __init__(self) -> None:
        self._dependencies: RetreatDependencies | None = None
        self._handler: RetreatHandler | None = None

    def configure(self, dependencies: RetreatDependencies) -> None:
        self._dependencies = dependencies
        self._handler = RetreatHandler(
            dependencies.telemetry,
            dependencies.translator,
        )

    def handler(self) -> RetreatHandler:
        if self._handler is not None:
            return self._handler
        if self._dependencies is None:
            raise RuntimeError("Retreat handler requires telemetry instrumentation")
        self.configure(self._dependencies)
        assert self._handler is not None
        return self._handler


_PROVIDER = RetreatHandlerProvider()


def configure_retreat(dependencies: RetreatDependencies) -> None:
    """Attach runtime helpers to the router provider."""

    _PROVIDER.configure(dependencies)


def _handler() -> RetreatHandler:
    return _PROVIDER.handler()


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def retreat(cb: CallbackQuery, navigator: NavigatorBack, **data: dict[str, Any]) -> None:
    handler = _handler()
    outcome: RetreatOutcome = await handler(cb, navigator, data)
    await cb.answer(outcome.text, show_alert=outcome.show_alert)


__all__ = [
    "router",
    "NavigatorBack",
    "retreat",
    "BACK_CALLBACK_DATA",
    "RetreatDependencies",
    "configure_retreat",
]

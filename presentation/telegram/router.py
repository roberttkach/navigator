from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Protocol

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


class RetreatCallback(Protocol):
    def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        **data: dict[str, Any],
    ) -> Awaitable[None]: ...


def build_retreat_handler(dependencies: RetreatDependencies) -> RetreatHandler:
    """Create a retreat handler with explicit dependencies."""

    return RetreatHandler(dependencies.telemetry, dependencies.translator)


def _retreat_callback(handler: RetreatHandler) -> RetreatCallback:
    async def _callback(
        cb: CallbackQuery,
        navigator: NavigatorBack,
        **data: dict[str, Any],
    ) -> None:
        outcome: RetreatOutcome = await handler(cb, navigator, data)
        await cb.answer(outcome.text, show_alert=outcome.show_alert)

    return _callback


@dataclass(slots=True)
class RetreatRouterConfigurator:
    """Install retreat callback handlers on a dedicated router."""

    router: Router

    def configure(self, dependencies: RetreatDependencies) -> RetreatCallback:
        handler = build_retreat_handler(dependencies)
        callback = _retreat_callback(handler)
        self.router.callback_query.register(callback, F.data == BACK_CALLBACK_DATA)
        return callback


def retreat_configurator(target: Router | None = None) -> RetreatRouterConfigurator:
    """Return a configurator bound to ``target`` or the module router."""

    return RetreatRouterConfigurator(target or router)


def configure_retreat(
    dependencies: RetreatDependencies,
    *,
    target: Router | None = None,
) -> RetreatCallback:
    """Attach retreat handling to ``target`` router and return the callback."""

    configurator = retreat_configurator(target)
    return configurator.configure(dependencies)


__all__ = [
    "router",
    "NavigatorBack",
    "BACK_CALLBACK_DATA",
    "RetreatDependencies",
    "RetreatCallback",
    "RetreatRouterConfigurator",
    "build_retreat_handler",
    "configure_retreat",
    "retreat_configurator",
]

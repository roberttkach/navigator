from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Awaitable, Protocol

from aiogram import F, Router
from aiogram.types import CallbackQuery

from navigator.core.telemetry import Telemetry
from navigator.presentation.alerts import lexeme
from navigator.presentation.telegram.back import (
    NavigatorBack,
    RetreatFailureNotes,
    RetreatFailureTranslator,
    RetreatHandler,
    RetreatOutcome,
    Translator,
    create_retreat_handler,
    default_retreat_providers,
)
from navigator.presentation.telegram.failures import (
    default_retreat_failure_notes,
    default_retreat_failure_translator,
)

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA = "back"


@dataclass(frozen=True)
class RetreatDependencies:
    """Dependencies required to configure retreat handling."""

    telemetry: Telemetry
    translator: Translator = lexeme
    failures: Callable[[], RetreatFailureTranslator] = field(
        default=default_retreat_failure_translator
    )
    notes: Callable[[], RetreatFailureNotes] = field(
        default=default_retreat_failure_notes
    )


class RetreatCallback(Protocol):
    def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        **data: dict[str, Any],
    ) -> Awaitable[None]: ...


def build_retreat_handler(dependencies: RetreatDependencies) -> RetreatHandler:
    """Create a retreat handler with explicit dependencies."""

    providers = default_retreat_providers(
        failures=dependencies.failures,
        notes=dependencies.notes,
    )
    return create_retreat_handler(
        dependencies.telemetry,
        dependencies.translator,
        providers=providers,
    )


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
class RetreatCallbackFactory:
    """Create retreat callbacks independent from router registration."""

    def create(self, dependencies: RetreatDependencies) -> RetreatCallback:
        handler = build_retreat_handler(dependencies)
        return _retreat_callback(handler)


@dataclass(slots=True)
class RetreatRouterInstaller:
    """Attach retreat callbacks to a router instance."""

    router: Router

    def install(self, callback: RetreatCallback) -> None:
        self.router.callback_query.register(callback, F.data == BACK_CALLBACK_DATA)


@dataclass(slots=True)
class RetreatRouterConfigurator:
    """Compose callback factories with router installers."""

    factory: RetreatCallbackFactory
    installer: RetreatRouterInstaller

    def configure(self, dependencies: RetreatDependencies) -> RetreatCallback:
        callback = self.factory.create(dependencies)
        self.installer.install(callback)
        return callback


def retreat_configurator(target: Router | None = None) -> RetreatRouterConfigurator:
    """Return a configurator bound to ``target`` or the module router."""

    installer = RetreatRouterInstaller(target or router)
    factory = RetreatCallbackFactory()
    return RetreatRouterConfigurator(factory=factory, installer=installer)


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
    "RetreatCallbackFactory",
    "RetreatRouterConfigurator",
    "RetreatRouterInstaller",
    "build_retreat_handler",
    "configure_retreat",
    "retreat_configurator",
]

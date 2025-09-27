from __future__ import annotations

from dataclasses import dataclass

from aiogram import F, Router

from navigator.presentation.telegram.back import NavigatorBack
from navigator.presentation.telegram.back.callbacks import RetreatCallback
from navigator.presentation.telegram.back.dependencies import RetreatDependencies
from navigator.presentation.telegram.back.setup import (
    RetreatCallbackFactory,
    RetreatHandlerBuilder,
    create_retreat_callback,
)

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA = "back"


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
    factory = RetreatCallbackFactory(builder=RetreatHandlerBuilder())
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
    "BACK_CALLBACK_DATA",
    "NavigatorBack",
    "RetreatCallback",
    "RetreatCallbackFactory",
    "RetreatDependencies",
    "RetreatHandlerBuilder",
    "RetreatRouterConfigurator",
    "RetreatRouterInstaller",
    "configure_retreat",
    "create_retreat_callback",
    "retreat_configurator",
]

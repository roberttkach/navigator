from __future__ import annotations

from typing import Callable, Protocol

from aiogram import Router

from navigator.contracts.runtime import NavigatorRuntimeBundleLike

from .router import RetreatDependencies, RetreatRouterConfigurator, retreat_configurator


class RetreatConfiguratorFactory(Protocol):
    """Protocol describing factories providing router configurators."""

    def __call__(
        self, bundle: NavigatorRuntimeBundleLike
    ) -> RetreatRouterConfigurator: ...


def build_retreat_instrument(
    factory: RetreatConfiguratorFactory,
) -> Callable[[NavigatorRuntimeBundleLike], None]:
    """Return an instrumentation hook using ``factory`` per runtime bundle."""

    def _instrument(bundle: NavigatorRuntimeBundleLike) -> None:
        configurator = factory(bundle)
        dependencies = RetreatDependencies(telemetry=bundle.telemetry)
        callback = configurator.build(dependencies)
        configurator.register(callback)

    return _instrument


def instrument_for_configurator(
    configurator: RetreatRouterConfigurator,
) -> Callable[[NavigatorRuntimeBundleLike], None]:
    """Return an instrumentation hook bound to ``configurator``."""

    def _factory(_: NavigatorRuntimeBundleLike) -> RetreatRouterConfigurator:
        return configurator

    return build_retreat_instrument(_factory)


def instrument_for_router(router: Router) -> Callable[[NavigatorRuntimeBundleLike], None]:
    """Return an instrumentation hook registering callbacks on ``router``."""

    def _factory(_: NavigatorRuntimeBundleLike) -> RetreatRouterConfigurator:
        return retreat_configurator(router)

    return build_retreat_instrument(_factory)


__all__ = [
    "build_retreat_instrument",
    "instrument_for_configurator",
    "instrument_for_router",
    "RetreatConfiguratorFactory",
]

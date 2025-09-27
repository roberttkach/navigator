from __future__ import annotations

from typing import Callable, Protocol

from navigator.app.service.navigator_runtime import NavigatorRuntimeBundleLike

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


def _default_factory(_: NavigatorRuntimeBundleLike) -> RetreatRouterConfigurator:
    """Return configurator bound to the module router by default."""

    return retreat_configurator()


instrument = build_retreat_instrument(_default_factory)


__all__ = ["instrument", "build_retreat_instrument", "RetreatConfiguratorFactory"]

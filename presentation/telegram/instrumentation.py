"""Bootstrap adapters for Telegram presentation components."""
from __future__ import annotations

from typing import Callable

from navigator.api.contracts import NavigatorRuntimeBundleLike

from .router import RetreatDependencies, RetreatRouterConfigurator, retreat_configurator


def build_retreat_instrument(
    configurator: RetreatRouterConfigurator,
) -> Callable[[NavigatorRuntimeBundleLike], None]:
    """Return an instrumentation hook bound to ``configurator`` router."""

    def _instrument(bundle: NavigatorRuntimeBundleLike) -> None:
        dependencies = RetreatDependencies(telemetry=bundle.telemetry)
        callback = configurator.build(dependencies)
        configurator.register(callback)

    return _instrument


instrument = build_retreat_instrument(retreat_configurator())


__all__ = ["instrument", "build_retreat_instrument"]

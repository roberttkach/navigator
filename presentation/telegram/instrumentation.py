"""Bootstrap adapters for Telegram presentation components."""
from __future__ import annotations

from navigator.bootstrap.navigator.runtime import NavigatorRuntimeBundle

from .router import RetreatDependencies, configure_retreat


def instrument(bundle: NavigatorRuntimeBundle) -> None:
    """Wire navigator runtime data into Telegram router configuration."""

    configure_retreat(RetreatDependencies(telemetry=bundle.telemetry))


__all__ = ["instrument"]

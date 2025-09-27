"""High level helpers composing retreat callbacks from dependencies."""
from __future__ import annotations

from dataclasses import dataclass

from .callbacks import RetreatCallback, adapt_retreat_handler
from .dependencies import RetreatDependencies
from .factory import create_retreat_handler
from .handler import RetreatHandler
from .providers import default_retreat_providers


@dataclass(slots=True)
class RetreatHandlerBuilder:
    """Build retreat handlers from presentation dependencies."""

    def build(self, dependencies: RetreatDependencies) -> RetreatHandler:
        providers = default_retreat_providers(
            failures=dependencies.failures,
            notes=dependencies.notes,
        )
        return create_retreat_handler(
            dependencies.telemetry,
            dependencies.translator,
            providers=providers,
        )


@dataclass(slots=True)
class RetreatCallbackFactory:
    """Create Telegram callbacks from handler builders."""

    builder: RetreatHandlerBuilder

    def create(self, dependencies: RetreatDependencies) -> RetreatCallback:
        handler = self.builder.build(dependencies)
        return adapt_retreat_handler(handler)


def create_retreat_callback(dependencies: RetreatDependencies) -> RetreatCallback:
    """Convenience helper returning a configured retreat callback."""

    factory = RetreatCallbackFactory(builder=RetreatHandlerBuilder())
    return factory.create(dependencies)


__all__ = [
    "RetreatCallbackFactory",
    "RetreatHandlerBuilder",
    "create_retreat_callback",
]

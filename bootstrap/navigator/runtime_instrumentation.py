"""Decorators applying instrumentation to runtime factories."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from navigator.contracts.runtime import NavigatorRuntimeInstrument

from .context import BootstrapContext
from .runtime import NavigatorFactory, NavigatorRuntimeBundle


@dataclass(slots=True)
class InstrumentationDecorator:
    """Decorate factories with runtime instrumentation hooks."""

    instruments: Sequence[NavigatorRuntimeInstrument]

    def apply(self, factory: NavigatorFactory) -> NavigatorFactory:
        if not self.instruments:
            return factory
        return InstrumentedNavigatorFactory(factory, self.instruments)


class InstrumentedNavigatorFactory(NavigatorFactory):
    """Decorate runtime factories with instrumentation hooks."""

    def __init__(
        self,
        base: NavigatorFactory,
        instrumentation: Sequence[NavigatorRuntimeInstrument],
    ) -> None:
        self._base = base
        self._instrumentation = instrumentation

    async def create(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        bundle = await self._base.create(context)
        for instrument in self._instrumentation:
            instrument(bundle)
        return bundle


__all__ = ["InstrumentationDecorator", "InstrumentedNavigatorFactory"]

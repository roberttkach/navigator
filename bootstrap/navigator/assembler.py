"""Assemblers orchestrating navigator runtime creation."""
from __future__ import annotations

from dataclasses import dataclass

from .context import BootstrapContext
from .runtime import NavigatorFactory, NavigatorRuntimeBundle
from .runtime_instrumentation import InstrumentationDecorator
from .runtime_resolution import RuntimeFactoryResolver


class NavigatorAssembler:
    """Compose navigator runtime bundles from bootstrap context."""

    def __init__(
        self,
        *,
        resolver: RuntimeFactoryResolver,
        decorator: InstrumentationDecorator,
        runtime_factory: NavigatorFactory | None = None,
    ) -> None:
        self._resolver = resolver
        self._decorator = decorator
        self._runtime_factory = runtime_factory

    async def build(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        base = self._resolver.resolve(
            runtime_factory=self._runtime_factory,
            context_view=context.view_container,
        )
        factory = self._decorator.apply(base)
        return await factory.create(context)


@dataclass(slots=True)
class NavigatorAssemblerBuilder:
    """Prepare assembler collaborators isolating configuration policies."""

    resolver: RuntimeFactoryResolver
    decorator: InstrumentationDecorator

    def create(self, runtime_factory: NavigatorFactory | None = None) -> NavigatorAssembler:
        return NavigatorAssembler(
            resolver=self.resolver,
            decorator=self.decorator,
            runtime_factory=runtime_factory,
        )


__all__ = ["NavigatorAssembler", "NavigatorAssemblerBuilder"]

"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from navigator.api.contracts import (
    NavigatorRuntimeInstrument,
    ScopeDTO,
    ViewLedgerDTO,
)
from navigator.core.contracts import MissingAlert
from .context import BootstrapContext, ViewContainerFactory
from .container_resolution import ContainerResolution, create_container_resolution
from .runtime import ContainerRuntimeFactory, NavigatorFactory, NavigatorRuntimeBundle


@dataclass(slots=True)
class ViewContainerResolver:
    """Resolve the view container using configured resolution policy."""

    resolution: ContainerResolution

    def resolve(self, candidate: ViewContainerFactory | None) -> ViewContainerFactory:
        if candidate is not None:
            return candidate
        return self.resolution.resolve_view_container()


@dataclass(slots=True)
class RuntimeFactoryBuilder:
    """Build navigator factories while isolating container resolution."""

    resolver: ViewContainerResolver

    def build(
        self,
        *,
        runtime_factory: NavigatorFactory | None,
        view_container: ViewContainerFactory | None,
    ) -> NavigatorFactory:
        if runtime_factory is not None:
            return runtime_factory
        container = self.resolver.resolve(view_container)
        return ContainerRuntimeFactory(view_container=container)


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


class NavigatorAssembler:
    """Compose navigator runtime bundles from bootstrap context."""

    def __init__(
        self,
        runtime_factory: NavigatorFactory | None = None,
        instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
        view_container: ViewContainerFactory | None = None,
        resolution: ContainerResolution | None = None,
    ) -> None:
        resolved = resolution or create_container_resolution()
        resolver = ViewContainerResolver(resolved)
        builder = RuntimeFactoryBuilder(resolver)
        factory = builder.build(
            runtime_factory=runtime_factory,
            view_container=view_container,
        )
        if instrumentation:
            factory = InstrumentedNavigatorFactory(factory, tuple(instrumentation))
        self._runtime_factory = factory

    async def build(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        return await self._runtime_factory.create(context)


async def assemble(
    *,
    event: object,
    state: object,
    ledger: ViewLedgerDTO,
    scope: ScopeDTO,
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    missing_alert: MissingAlert | None = None,
    view_container: ViewContainerFactory | None = None,
    resolution: ContainerResolution | None = None,
) -> NavigatorRuntimeBundle:
    """Construct a navigator runtime bundle from entrypoint payloads."""

    context = BootstrapContext(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        missing_alert=missing_alert,
        view_container=view_container,
    )
    instruments: Sequence[NavigatorRuntimeInstrument]
    if instrumentation:
        instruments = tuple(instrumentation)
    else:
        instruments = ()
    assembler = NavigatorAssembler(
        instrumentation=instruments,
        view_container=view_container,
        resolution=resolution,
    )
    return await assembler.build(context)


__all__ = [
    "InstrumentedNavigatorFactory",
    "NavigatorAssembler",
    "RuntimeFactoryBuilder",
    "ViewContainerResolver",
    "assemble",
]

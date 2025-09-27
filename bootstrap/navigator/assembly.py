"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from navigator.app.service.navigator_runtime.api_contracts import (
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .context import BootstrapContext, ViewContainerFactory
from .container_resolution import ContainerResolution, create_container_resolution
from .instrumentation import as_sequence
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
class RuntimeFactoryResolver:
    """Resolve runtime factories from bootstrap collaborators."""

    view_resolver: ViewContainerResolver
    default_view: ViewContainerFactory | None = None

    def resolve(
        self,
        *,
        runtime_factory: NavigatorFactory | None,
        context_view: ViewContainerFactory | None,
    ) -> NavigatorFactory:
        if runtime_factory is not None:
            return runtime_factory
        candidate = context_view or self.default_view
        container = self.view_resolver.resolve(candidate)
        return ContainerRuntimeFactory(view_container=container)


@dataclass(slots=True)
class InstrumentationDecorator:
    """Decorate factories with runtime instrumentation hooks."""

    instruments: Sequence[NavigatorRuntimeInstrument]

    def apply(self, factory: NavigatorFactory) -> NavigatorFactory:
        if not self.instruments:
            return factory
        return InstrumentedNavigatorFactory(factory, self.instruments)


@dataclass(slots=True)
class BootstrapContextFactory:
    """Construct bootstrap context objects from raw payloads."""

    def create(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        missing_alert: MissingAlert | None,
        view_container: ViewContainerFactory | None,
    ) -> BootstrapContext:
        return BootstrapContext(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            missing_alert=missing_alert,
            view_container=view_container,
        )


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
        *,
        instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
        view_container: ViewContainerFactory | None = None,
        resolution: ContainerResolution | None = None,
        factory_resolver: RuntimeFactoryResolver | None = None,
        decorator: InstrumentationDecorator | None = None,
    ) -> None:
        resolved = resolution or create_container_resolution()
        resolver = factory_resolver or RuntimeFactoryResolver(
            ViewContainerResolver(resolved),
            default_view=view_container,
        )
        self._resolver = resolver
        instruments = instrumentation or ()
        self._decorator = decorator or InstrumentationDecorator(tuple(instruments))
        self._runtime_factory = runtime_factory

    async def build(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        base = self._resolver.resolve(
            runtime_factory=self._runtime_factory,
            context_view=context.view_container,
        )
        factory = self._decorator.apply(base)
        return await factory.create(context)


async def assemble(
    *,
    event: object,
    state: object,
    ledger: ViewLedger,
    scope: Scope,
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    missing_alert: MissingAlert | None = None,
    view_container: ViewContainerFactory | None = None,
    resolution: ContainerResolution | None = None,
) -> NavigatorRuntimeBundle:
    """Construct a navigator runtime bundle from entrypoint payloads."""

    context = BootstrapContextFactory().create(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        missing_alert=missing_alert,
        view_container=view_container,
    )
    instruments = as_sequence(instrumentation)
    assembler = NavigatorAssembler(
        instrumentation=instruments,
        view_container=view_container,
        resolution=resolution,
    )
    return await assembler.build(context)


__all__ = [
    "BootstrapContextFactory",
    "InstrumentationDecorator",
    "InstrumentedNavigatorFactory",
    "NavigatorAssembler",
    "RuntimeFactoryResolver",
    "ViewContainerResolver",
    "assemble",
]

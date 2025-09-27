"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from navigator.contracts.runtime import NavigatorRuntimeInstrument
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

    @classmethod
    def configure(
        cls,
        *,
        instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
        view_container: ViewContainerFactory | None = None,
        resolution: ContainerResolution | None = None,
        resolver: RuntimeFactoryResolver | None = None,
        decorator: InstrumentationDecorator | None = None,
    ) -> "NavigatorAssemblerBuilder":
        resolved_resolution = resolution or create_container_resolution()
        resolved_resolver = resolver or RuntimeFactoryResolver(
            ViewContainerResolver(resolved_resolution),
            default_view=view_container,
        )
        instruments = instrumentation or ()
        resolved_decorator = decorator or InstrumentationDecorator(tuple(instruments))
        return cls(resolver=resolved_resolver, decorator=resolved_decorator)


async def assemble(
    *,
    event: object,
    state: object,
    ledger: ViewLedger,
    scope: Scope,
    runtime_factory: NavigatorFactory | None = None,
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    missing_alert: MissingAlert | None = None,
    view_container: ViewContainerFactory | None = None,
    resolution: ContainerResolution | None = None,
) -> NavigatorRuntimeBundle:
    """High level entrypoint assembling navigator runtime bundles."""

    builder = NavigatorAssemblerBuilder.configure(
        instrumentation=instrumentation,
        view_container=view_container,
        resolution=resolution,
    )
    assembler = builder.create(runtime_factory)
    context = BootstrapContext(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        missing_alert=missing_alert,
        view_container=view_container,
    )
    return await assembler.build(context)


__all__ = [
    "assemble",
    "BootstrapContextFactory",
    "InstrumentationDecorator",
    "NavigatorAssembler",
    "NavigatorAssemblerBuilder",
    "RuntimeFactoryResolver",
    "ViewContainerResolver",
]

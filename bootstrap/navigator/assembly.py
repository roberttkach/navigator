"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from navigator.contracts.runtime import NavigatorRuntimeInstrument
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .assembler import NavigatorAssemblerBuilder
from .context_factory import BootstrapContextFactory
from .instrumentation import as_sequence
from .runtime import NavigatorFactory, NavigatorRuntimeBundle
from .runtime_instrumentation import InstrumentationDecorator
from .runtime_resolution import RuntimeFactoryResolver, create_runtime_factory_resolver

if TYPE_CHECKING:
    from .container_resolution import ContainerResolution
    from .context import ViewContainerFactory


@dataclass(slots=True)
class AssemblerServices:
    """Group collaborators required to construct navigator assemblers."""

    resolver: RuntimeFactoryResolver
    decorator: InstrumentationDecorator
    context_factory: BootstrapContextFactory

    def builder(self) -> NavigatorAssemblerBuilder:
        return NavigatorAssemblerBuilder(resolver=self.resolver, decorator=self.decorator)


def create_assembler_services(
    *,
    instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
    view_container: ViewContainerFactory | None = None,
    resolution: ContainerResolution | None = None,
    resolver: RuntimeFactoryResolver | None = None,
    decorator: InstrumentationDecorator | None = None,
    context_factory: BootstrapContextFactory | None = None,
) -> AssemblerServices:
    """Resolve assembler dependencies into a single configuration object."""

    instruments = instrumentation or ()
    resolved_resolver = create_runtime_factory_resolver(
        resolution=resolution,
        default_view=view_container,
        resolver=resolver,
    )
    resolved_decorator = decorator or InstrumentationDecorator(tuple(instruments))
    resolved_context_factory = context_factory or BootstrapContextFactory()
    return AssemblerServices(
        resolver=resolved_resolver,
        decorator=resolved_decorator,
        context_factory=resolved_context_factory,
    )


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
    context_factory: BootstrapContextFactory | None = None,
) -> NavigatorRuntimeBundle:
    """High level entrypoint assembling navigator runtime bundles."""

    services = create_assembler_services(
        instrumentation=as_sequence(instrumentation),
        view_container=view_container,
        resolution=resolution,
        context_factory=context_factory,
    )
    builder = services.builder()
    assembler = builder.create(runtime_factory)
    context = services.context_factory.create(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        missing_alert=missing_alert,
        view_container=view_container,
    )
    return await assembler.build(context)


__all__ = [
    "AssemblerServices",
    "BootstrapContextFactory",
    "InstrumentationDecorator",
    "NavigatorAssemblerBuilder",
    "NavigatorFactory",
    "NavigatorRuntimeBundle",
    "RuntimeFactoryResolver",
    "assemble",
    "create_assembler_services",
]

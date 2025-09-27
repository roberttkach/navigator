"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

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


class NavigatorAssembler:
    """Compose navigator runtime bundles from bootstrap context."""

    def __init__(
        self,
        runtime_factory: NavigatorFactory | None = None,
        instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
        view_container: ViewContainerFactory | None = None,
        resolution: ContainerResolution | None = None,
    ) -> None:
        self._resolution = resolution or create_container_resolution()
        container = _resolve_view_container(view_container, self._resolution)
        factory = runtime_factory or ContainerRuntimeFactory(view_container=container)
        self._runtime_factory = factory
        if instrumentation:
            self._instrumentation = tuple(instrumentation)
        else:
            self._instrumentation = ()

    async def build(self, context: BootstrapContext) -> NavigatorRuntimeBundle:
        bundle = await self._runtime_factory.create(context)
        for instrument in self._instrumentation:
            instrument(bundle)
        return bundle


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


def _resolve_view_container(
    candidate: ViewContainerFactory | None,
    resolution: ContainerResolution,
) -> ViewContainerFactory:
    """Resolve the concrete view container lazily to avoid heavy imports."""

    if candidate is not None:
        return candidate
    return resolution.resolve_view_container()


__all__ = ["NavigatorAssembler", "assemble"]

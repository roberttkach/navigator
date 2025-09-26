"""Top-level assembly entrypoints orchestrating runtime creation."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from navigator.api.contracts import (
    NavigatorRuntimeInstrument,
    ScopeDTO,
    ViewLedgerDTO,
)
from navigator.app.service.navigator_runtime import MissingAlert
from .context import BootstrapContext
from .runtime import ContainerRuntimeFactory, NavigatorFactory, NavigatorRuntimeBundle


class NavigatorAssembler:
    """Compose navigator runtime bundles from bootstrap context."""

    def __init__(
        self,
        runtime_factory: NavigatorFactory | None = None,
        instrumentation: Sequence[NavigatorRuntimeInstrument] | None = None,
    ) -> None:
        self._runtime_factory = runtime_factory or ContainerRuntimeFactory()
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
) -> NavigatorRuntimeBundle:
    """Construct a navigator runtime bundle from entrypoint payloads."""

    context = BootstrapContext(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        missing_alert=missing_alert,
    )
    instruments: Sequence[NavigatorRuntimeInstrument]
    if instrumentation:
        instruments = tuple(instrumentation)
    else:
        instruments = ()
    assembler = NavigatorAssembler(instrumentation=instruments)
    return await assembler.build(context)


__all__ = ["NavigatorAssembler", "assemble"]

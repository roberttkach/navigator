"""Bootstrap-backed implementation of the runtime assembly port."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.bootstrap.navigator import assemble as bootstrap_assemble
from navigator.bootstrap.navigator.instrumentation import as_sequence

from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
from navigator.app.service.navigator_runtime.runtime_assembly_port import (
    RuntimeAssemblyPort,
    RuntimeAssemblyRequest,
)


def _view_container_override(overrides: "NavigatorAssemblyOverrides" | None):
    if overrides is None:
        return None
    return overrides.view_container


@dataclass(slots=True)
class BootstrapRuntimeAssembler(RuntimeAssemblyPort[RuntimeAssemblyRequest]):
    """Delegate runtime assembly to the bootstrap package."""

    async def assemble(self, request: RuntimeAssemblyRequest) -> NavigatorRuntime:
        bundle = await bootstrap_assemble(
            event=request.event,
            state=request.state,
            ledger=request.ledger,
            scope=request.scope,
            instrumentation=as_sequence(request.instrumentation),
            missing_alert=request.missing_alert,
            view_container=_view_container_override(request.overrides),
            resolution=request.resolution,
        )
        return bundle.runtime


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - typing support only
        from navigator.contracts.runtime import NavigatorAssemblyOverrides


__all__ = ["BootstrapRuntimeAssembler"]

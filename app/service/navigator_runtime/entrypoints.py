"""Application-level entrypoints for assembling navigator facades."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Type, TypeVar

from navigator.bootstrap.navigator import assemble as bootstrap_assemble
from navigator.bootstrap.navigator.container_resolution import ContainerResolution
from navigator.bootstrap.navigator.context import ViewContainerFactory
from navigator.bootstrap.navigator.instrumentation import as_sequence
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .api_contracts import NavigatorAssemblyOverrides, NavigatorRuntimeInstrument
from .facade import NavigatorFacade

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


def _override_view_container(
    overrides: NavigatorAssemblyOverrides | None,
) -> ViewContainerFactory | None:
    if overrides is None:
        return None
    return overrides.view_container


async def assemble_navigator(
    *,
    event: object,
    state: object,
    ledger: ViewLedger,
    scope: Scope,
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    missing_alert: MissingAlert | None = None,
    overrides: NavigatorAssemblyOverrides | None = None,
    resolution: ContainerResolution | None = None,
    facade_type: Type[FacadeT] = NavigatorFacade,
) -> FacadeT:
    """Assemble a navigator facade for the provided runtime inputs."""

    bundle = await bootstrap_assemble(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=as_sequence(instrumentation),
        missing_alert=missing_alert,
        view_container=_override_view_container(overrides),
        resolution=resolution,
    )
    navigator = facade_type(bundle.runtime)
    return navigator


__all__ = ["assemble_navigator"]

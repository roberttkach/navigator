"""High level entrypoints orchestrating navigator runtime assembly."""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Type, TypeVar

from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .assembly_service import NavigatorAssemblyService, resolve_assembly_service
from .facade import NavigatorFacade
from .facade_factory import NavigatorFacadeFactory
from .request_factory import RuntimeAssemblyRequestFactory
from .runtime_assembly_port import RuntimeAssemblyPort, RuntimeAssemblyRequest
from .runtime_assembly_resolver import (
    RuntimeAssemblerResolver,
    RuntimeAssemblyProvider,
)

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


async def assemble_navigator(
    *,
    event: object,
    state: object,
    ledger: ViewLedger,
    scope: Scope,
    instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    missing_alert: MissingAlert | None = None,
    overrides: NavigatorAssemblyOverrides | None = None,
    resolution: "ContainerResolution" | None = None,
    facade_type: Type[FacadeT] = NavigatorFacade,
    assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None = None,
    provider: RuntimeAssemblyProvider | None = None,
    request_factory: RuntimeAssemblyRequestFactory | None = None,
    assembler_resolver: RuntimeAssemblerResolver | None = None,
    facade_factory: NavigatorFacadeFactory[FacadeT] | None = None,
) -> FacadeT:
    """Assemble a navigator facade for the provided runtime inputs."""

    service = resolve_assembly_service(
        provider=provider,
        request_factory=request_factory,
        assembler_resolver=assembler_resolver,
        facade_factory=facade_factory,
    )
    return await service.assemble(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=instrumentation,
        missing_alert=missing_alert,
        overrides=overrides,
        resolution=resolution,
        facade_type=facade_type,
        assembler=assembler,
    )


__all__ = [
    "NavigatorAssemblyService",
    "NavigatorFacadeFactory",
    "RuntimeAssemblyRequestFactory",
    "resolve_assembly_service",
    "assemble_navigator",
]


if TYPE_CHECKING:  # pragma: no cover - typing support only
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution
    from .runtime import NavigatorRuntime

from collections.abc import Iterable
from typing import TYPE_CHECKING, Type, TypeVar

from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .facade import NavigatorFacade
from .runtime_assembly_port import RuntimeAssemblyPort, RuntimeAssemblyRequest
from .runtime_assembly_resolver import (
    RuntimeAssemblyProvider,
    resolve_runtime_assembler,
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
) -> FacadeT:
    """Assemble a navigator facade for the provided runtime inputs."""

    request = RuntimeAssemblyRequest(
        event=event,
        state=state,
        ledger=ledger,
        scope=scope,
        instrumentation=instrumentation,
        missing_alert=missing_alert,
        overrides=overrides,
        resolution=resolution,
    )
    runtime_assembler = resolve_runtime_assembler(
        assembler=assembler,
        provider=provider,
        resolution=resolution,
    )
    runtime = await runtime_assembler.assemble(request)
    navigator = facade_type(runtime)
    return navigator


__all__ = ["assemble_navigator"]


if TYPE_CHECKING:  # pragma: no cover - typing support only
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution

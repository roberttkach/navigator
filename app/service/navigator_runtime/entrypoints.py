from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Type, TypeVar

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
    RuntimeAssemblerResolver,
    RuntimeAssemblyProvider,
)

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


@dataclass(frozen=True)
class RuntimeAssemblyRequestFactory:
    """Create runtime assembly requests from presentation inputs."""

    def create(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None,
        missing_alert: MissingAlert | None,
        overrides: NavigatorAssemblyOverrides | None,
        resolution: "ContainerResolution" | None,
    ) -> RuntimeAssemblyRequest:
        return RuntimeAssemblyRequest(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=instrumentation,
            missing_alert=missing_alert,
            overrides=overrides,
            resolution=resolution,
        )


@dataclass(frozen=True)
class NavigatorFacadeFactory(Generic[FacadeT]):
    """Create navigator facades from assembled runtimes."""

    def create(self, runtime: "NavigatorRuntime", facade_type: Type[FacadeT]) -> FacadeT:
        return facade_type(runtime)


@dataclass(frozen=True)
class NavigatorAssemblyService(Generic[FacadeT]):
    """Coordinate request creation, assembler resolution and facade instantiation."""

    request_factory: RuntimeAssemblyRequestFactory
    resolver: RuntimeAssemblerResolver
    facade_factory: NavigatorFacadeFactory[FacadeT]

    async def assemble(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None,
        missing_alert: MissingAlert | None,
        overrides: NavigatorAssemblyOverrides | None,
        resolution: "ContainerResolution" | None,
        facade_type: Type[FacadeT],
        assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None,
    ) -> FacadeT:
        request = self.request_factory.create(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=instrumentation,
            missing_alert=missing_alert,
            overrides=overrides,
            resolution=resolution,
        )
        runtime_assembler = self.resolver.resolve(
            assembler=assembler,
            resolution=resolution,
        )
        runtime = await runtime_assembler.assemble(request)
        return self.facade_factory.create(runtime, facade_type)


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

    request_builder = request_factory or RuntimeAssemblyRequestFactory()
    facade_builder = facade_factory or NavigatorFacadeFactory()
    resolver = assembler_resolver
    if resolver is None:
        if provider is None:
            raise RuntimeError("Runtime assembler provider is not configured")
        resolver = RuntimeAssemblerResolver(provider=provider)
    runtime_resolver = resolver
    navigator_service: NavigatorAssemblyService[FacadeT] = NavigatorAssemblyService(
        request_factory=request_builder,
        resolver=runtime_resolver,
        facade_factory=facade_builder,
    )
    return await navigator_service.assemble(
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
    "assemble_navigator",
]


if TYPE_CHECKING:  # pragma: no cover - typing support only
    from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution

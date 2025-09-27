"""Orchestration services coordinating navigator runtime assembly."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Type, TypeVar

from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .facade import NavigatorFacade
from .facade_factory import NavigatorFacadeFactory
from .request_factory import RuntimeAssemblyRequestFactory
from .runtime_assembly_port import RuntimeAssemblyPort, RuntimeAssemblyRequest
from .runtime_assembly_resolver import (
    RuntimeAssemblerResolver,
    RuntimeAssemblyProvider,
)

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


@dataclass(frozen=True)
class RuntimeAssemblyPipeline:
    """Encapsulate the steps required to assemble a runtime instance."""

    request_factory: RuntimeAssemblyRequestFactory
    resolver: RuntimeAssemblerResolver

    def build_request(
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
        return self.request_factory.create(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=instrumentation,
            missing_alert=missing_alert,
            overrides=overrides,
            resolution=resolution,
        )

    def resolve_assembler(
        self,
        *,
        assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None,
        resolution: "ContainerResolution" | None,
    ) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
        return self.resolver.resolve(
            assembler=assembler,
            resolution=resolution,
        )

    async def assemble_runtime(
        self,
        request: RuntimeAssemblyRequest,
        assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest],
    ) -> object:
        return await assembler.assemble(request)


@dataclass(frozen=True)
class NavigatorAssemblyService(Generic[FacadeT]):
    """Coordinate runtime assembly through a pipeline and compose facades."""

    pipeline: RuntimeAssemblyPipeline
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
        request = self.pipeline.build_request(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=instrumentation,
            missing_alert=missing_alert,
            overrides=overrides,
            resolution=resolution,
        )
        runtime_assembler = self.pipeline.resolve_assembler(
            assembler=assembler,
            resolution=resolution,
        )
        runtime = await self.pipeline.assemble_runtime(request, runtime_assembler)
        return self.facade_factory.create(runtime, facade_type)


def resolve_assembly_service(
    *,
    provider: RuntimeAssemblyProvider | None,
    request_factory: RuntimeAssemblyRequestFactory | None,
    assembler_resolver: RuntimeAssemblerResolver | None,
    facade_factory: NavigatorFacadeFactory[FacadeT] | None,
) -> NavigatorAssemblyService[FacadeT]:
    """Instantiate a navigator assembly service with resolved collaborators."""

    request_builder = request_factory or RuntimeAssemblyRequestFactory()
    facade_builder = facade_factory or NavigatorFacadeFactory()
    resolver = _resolve_resolver(
        provider=provider,
        assembler_resolver=assembler_resolver,
    )
    pipeline = RuntimeAssemblyPipeline(
        request_factory=request_builder,
        resolver=resolver,
    )
    return NavigatorAssemblyService(
        pipeline=pipeline,
        facade_factory=facade_builder,
    )


def _resolve_resolver(
    *,
    provider: RuntimeAssemblyProvider | None,
    assembler_resolver: RuntimeAssemblerResolver | None,
) -> RuntimeAssemblerResolver:
    if assembler_resolver is not None:
        return assembler_resolver
    if provider is None:
        raise RuntimeError("Runtime assembler provider is not configured")
    return RuntimeAssemblerResolver(provider=provider)


__all__ = [
    "NavigatorAssemblyService",
    "RuntimeAssemblyPipeline",
    "resolve_assembly_service",
]


if False:  # pragma: no cover - typing only
    from collections.abc import Iterable
    from typing import TypeVar

    from .facade import NavigatorFacade
    from navigator.bootstrap.navigator.container_resolution import ContainerResolution

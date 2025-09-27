"""Adapters exposing navigator assembly for presentation layers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from navigator.contracts.runtime import NavigatorAssemblyOverrides, NavigatorRuntimeInstrument
from navigator.core.contracts import MissingAlert
from navigator.core.port.factory import ViewLedger
from navigator.core.value.message import Scope

from .facade import NavigatorFacade
from .runtime_assembly_resolver import RuntimeAssemblerResolver, RuntimeAssemblyProvider

FacadeT = TypeVar("FacadeT", bound=NavigatorFacade)


class RuntimeAssemblyEntrypoint(Protocol, Generic[FacadeT]):
    async def __call__(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
        instrumentation: tuple[NavigatorRuntimeInstrument, ...] | None = None,
        missing_alert: MissingAlert | None = None,
        overrides: NavigatorAssemblyOverrides | None = None,
        facade_type: type[FacadeT] | None = None,
    ) -> FacadeT: ...


@dataclass(frozen=True)
class RuntimeAssemblyConfiguration(Generic[FacadeT]):
    """Capture fixed assembly parameters shared by presentation adapters."""

    instrumentation: tuple[NavigatorRuntimeInstrument, ...]
    missing_alert: MissingAlert | None = None
    overrides: NavigatorAssemblyOverrides | None = None
    facade_type: type[FacadeT] | None = None
    assembler_resolver: RuntimeAssemblerResolver | None = None
    provider: RuntimeAssemblyProvider | None = None


class NavigatorRuntimeProvider(Generic[FacadeT]):
    """Provide presentation-oriented access to navigator assembly entrypoints."""

    def __init__(
        self,
        entrypoint: RuntimeAssemblyEntrypoint[FacadeT],
        *,
        configuration: RuntimeAssemblyConfiguration[FacadeT],
    ) -> None:
        self._entrypoint = entrypoint
        self._configuration = configuration

    async def assemble(
        self,
        *,
        event: object,
        state: object,
        ledger: ViewLedger,
        scope: Scope,
    ) -> FacadeT:
        """Assemble a navigator facade using the configured entrypoint."""

        return await self._entrypoint(
            event=event,
            state=state,
            ledger=ledger,
            scope=scope,
            instrumentation=self._configuration.instrumentation,
            missing_alert=self._configuration.missing_alert,
            overrides=self._configuration.overrides,
            facade_type=self._configuration.facade_type,
            assembler_resolver=self._configuration.assembler_resolver,
            provider=self._configuration.provider,
        )


def default_configuration(
    *,
    instrumentation: tuple[NavigatorRuntimeInstrument, ...] | None = None,
    missing_alert: MissingAlert | None = None,
    overrides: NavigatorAssemblyOverrides | None = None,
    facade_type: type[FacadeT] | None = None,
    assembler_resolver: RuntimeAssemblerResolver | None = None,
    provider: RuntimeAssemblyProvider | None = None,
) -> RuntimeAssemblyConfiguration[FacadeT]:
    """Return a configuration tuple normalising instrumentation payloads."""

    instruments = instrumentation or ()
    return RuntimeAssemblyConfiguration(
        instrumentation=instruments,
        missing_alert=missing_alert,
        overrides=overrides,
        facade_type=facade_type,
        assembler_resolver=assembler_resolver,
        provider=provider,
    )


__all__ = [
    "NavigatorRuntimeProvider",
    "RuntimeAssemblyConfiguration",
    "RuntimeAssemblyEntrypoint",
    "default_configuration",
]

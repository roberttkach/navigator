"""Runtime dependency wiring specific to the Telegram presentation layer."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Iterable

from navigator.contracts.runtime import NavigatorRuntimeInstrument

from navigator.app.service.navigator_runtime import (
    RuntimeAssemblyEntrypoint,
    RuntimeAssemblerResolver,
    RuntimeAssemblyProvider,
    assemble_navigator,
)

from .configuration import TelegramInstrumentationPolicy
from ..runtime_defaults import default_runtime_resolver


@dataclass(frozen=True)
class TelegramAssemblyCollaborators:
    """Capture collaborators required to assemble a runtime."""

    assembler_resolver: RuntimeAssemblerResolver | None
    provider: RuntimeAssemblyProvider | None
    entrypoint: RuntimeAssemblyEntrypoint

    @classmethod
    def create(
        cls,
        *,
        runtime_resolver: RuntimeAssemblerResolver | None = None,
        assembly_provider: RuntimeAssemblyProvider | None = None,
        entrypoint: RuntimeAssemblyEntrypoint | None = None,
    ) -> "TelegramAssemblyCollaborators":
        resolver = runtime_resolver or default_runtime_resolver()
        return cls(
            assembler_resolver=resolver,
            provider=assembly_provider,
            entrypoint=entrypoint or assemble_navigator,
        )


@dataclass(frozen=True)
class TelegramRuntimeDependencies:
    """Group runtime collaborators with instrumentation policies."""

    instrumentation: TelegramInstrumentationPolicy
    assembly: TelegramAssemblyCollaborators

    @classmethod
    def create(
        cls,
        *,
        instrumentation_factory: Callable[[], Iterable[NavigatorRuntimeInstrument]] | None = None,
        runtime_resolver: RuntimeAssemblerResolver | None = None,
        assembly_provider: RuntimeAssemblyProvider | None = None,
        entrypoint: RuntimeAssemblyEntrypoint | None = None,
    ) -> "TelegramRuntimeDependencies":
        instrumentation = TelegramInstrumentationPolicy.create(
            factory=instrumentation_factory
        )
        assembly = TelegramAssemblyCollaborators.create(
            runtime_resolver=runtime_resolver,
            assembly_provider=assembly_provider,
            entrypoint=entrypoint,
        )
        return cls(instrumentation=instrumentation, assembly=assembly)


__all__ = [
    "TelegramAssemblyCollaborators",
    "TelegramRuntimeDependencies",
]

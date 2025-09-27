"""Runtime provider utilities tailored for Telegram presentation layer."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from navigator.app.service.navigator_runtime import (
    NavigatorRuntimeProvider,
    RuntimeAssemblyConfiguration,
    RuntimeAssemblyEntrypoint,
    RuntimeAssemblyProvider,
    RuntimeAssemblerResolver,
    assemble_navigator,
    default_configuration,
)
from navigator.contracts.runtime import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeInstrument,
)
from navigator.core.contracts import MissingAlert

from .alerts import missing
from .runtime_defaults import (
    default_instrumentation_factory,
    default_runtime_resolver,
)


@dataclass(frozen=True)
class TelegramRuntimeConfiguration:
    """Configuration bundle describing runtime assembly policies."""

    instrumentation: Sequence[NavigatorRuntimeInstrument]
    missing_alert: MissingAlert
    facade_type: type | None = None
    assembler_resolver: RuntimeAssemblerResolver | None = None
    provider: RuntimeAssemblyProvider | None = None

    @classmethod
    def create(
        cls,
        *,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        missing_alert: MissingAlert | None = None,
        instrumentation_factory: Callable[[], Iterable[NavigatorRuntimeInstrument]] | None = None,
        facade_type: type | None = None,
        assembler_resolver: RuntimeAssemblerResolver | None = None,
        provider: RuntimeAssemblyProvider | None = None,
    ) -> "TelegramRuntimeConfiguration":
        instruments: Sequence[NavigatorRuntimeInstrument]
        if instrumentation is None:
            candidates = instrumentation_factory() if instrumentation_factory else ()
            instruments = tuple(candidates)
        else:
            instruments = tuple(instrumentation)
        return cls(
            instrumentation=instruments,
            missing_alert=missing_alert or missing,
            facade_type=facade_type,
            assembler_resolver=assembler_resolver,
            provider=provider,
        )

    def as_configuration(
        self, overrides: NavigatorAssemblyOverrides | None
    ) -> RuntimeAssemblyConfiguration:
        """Translate Telegram configuration into a runtime configuration."""

        return default_configuration(
            instrumentation=tuple(self.instrumentation),
            missing_alert=self.missing_alert,
            overrides=overrides,
            facade_type=self.facade_type,
            assembler_resolver=self.assembler_resolver,
            provider=self.provider,
        )


@dataclass(frozen=True)
class TelegramRuntimeDependencies:
    """Resolve runtime assembly collaborators for the Telegram façade."""

    instrumentation_factory: Callable[[], Iterable[NavigatorRuntimeInstrument]]
    assembler_resolver: RuntimeAssemblerResolver | None
    provider: RuntimeAssemblyProvider | None
    entrypoint: RuntimeAssemblyEntrypoint | None = None

    @classmethod
    def create(
        cls,
        *,
        instrumentation_factory: Callable[
            [], Iterable[NavigatorRuntimeInstrument]
        ] | None = None,
        runtime_resolver: RuntimeAssemblerResolver | None = None,
        assembly_provider: RuntimeAssemblyProvider | None = None,
        entrypoint: RuntimeAssemblyEntrypoint | None = None,
    ) -> "TelegramRuntimeDependencies":
        """Build a dependency bundle using presentation defaults where required."""

        factory = instrumentation_factory or default_instrumentation_factory
        resolver = runtime_resolver or default_runtime_resolver()
        return cls(
            instrumentation_factory=factory,
            assembler_resolver=resolver,
            provider=assembly_provider,
            entrypoint=entrypoint or assemble_navigator,
        )

    def configuration(
        self,
        *,
        base: TelegramRuntimeConfiguration | None = None,
        facade_type: type | None = None,
    ) -> TelegramRuntimeConfiguration:
        """Return a runtime configuration resolved from provided dependencies."""

        if base is not None:
            return base
        return TelegramRuntimeConfiguration.create(
            instrumentation_factory=self.instrumentation_factory,
            assembler_resolver=self.assembler_resolver,
            provider=self.provider,
            facade_type=facade_type,
        )


@dataclass(frozen=True)
class TelegramRuntimeProviderFactory:
    """Create runtime providers bound to Telegram defaults."""

    dependencies: TelegramRuntimeDependencies

    def create(
        self,
        *,
        configuration: TelegramRuntimeConfiguration,
        overrides: NavigatorAssemblyOverrides | None,
        provider: NavigatorRuntimeProvider | None,
    ) -> NavigatorRuntimeProvider:
        if provider is not None:
            return provider
        runtime_configuration = configuration.as_configuration(overrides)
        entrypoint = self.dependencies.entrypoint or assemble_navigator
        return NavigatorRuntimeProvider(
            entrypoint,
            configuration=runtime_configuration,
        )


NavigatorInstrument = NavigatorRuntimeInstrument
RuntimeResolver = RuntimeAssemblerResolver
AssemblyProvider = RuntimeAssemblyProvider
RuntimeEntrypoint = RuntimeAssemblyEntrypoint


__all__ = [
    "NavigatorInstrument",
    "RuntimeResolver",
    "RuntimeEntrypoint",
    "AssemblyProvider",
    "TelegramRuntimeConfiguration",
    "TelegramRuntimeDependencies",
    "TelegramRuntimeProviderFactory",
]

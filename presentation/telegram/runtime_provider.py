"""Runtime provider utilities tailored for Telegram presentation layer."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace

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
class TelegramInstrumentationPolicy:
    """Describe how instrumentation for the runtime should be produced."""

    factory: Callable[[], Iterable[NavigatorRuntimeInstrument]]

    @classmethod
    def create(
        cls,
        factory: Callable[[], Iterable[NavigatorRuntimeInstrument]] | None = None,
    ) -> "TelegramInstrumentationPolicy":
        return cls(factory=factory or default_instrumentation_factory)


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
        instrumentation_factory: Callable[
            [], Iterable[NavigatorRuntimeInstrument]
        ] | None = None,
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


@dataclass(frozen=True)
class TelegramRuntimeConfigurationResolver:
    """Resolve configuration objects using the provided dependencies."""

    dependencies: TelegramRuntimeDependencies

    def resolve(
        self,
        *,
        base: TelegramRuntimeConfiguration | None = None,
        facade_type: type | None = None,
    ) -> TelegramRuntimeConfiguration:
        if base is not None:
            return base
        return TelegramRuntimeConfiguration.create(
            instrumentation_factory=self.dependencies.instrumentation.factory,
            assembler_resolver=self.dependencies.assembly.assembler_resolver,
            provider=self.dependencies.assembly.provider,
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
        return NavigatorRuntimeProvider(
            self.dependencies.assembly.entrypoint,
            configuration=runtime_configuration,
        )


@dataclass(frozen=True)
class TelegramRuntimeBuilder:
    """Orchestrate the construction of navigator runtime providers."""

    dependencies: TelegramRuntimeDependencies
    configuration_resolver: TelegramRuntimeConfigurationResolver

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
    ) -> "TelegramRuntimeBuilder":
        dependencies = TelegramRuntimeDependencies.create(
            instrumentation_factory=instrumentation_factory,
            runtime_resolver=runtime_resolver,
            assembly_provider=assembly_provider,
            entrypoint=entrypoint,
        )
        configuration_resolver = TelegramRuntimeConfigurationResolver(dependencies)
        return cls(
            dependencies=dependencies,
            configuration_resolver=configuration_resolver,
        )

    def build_provider(
        self,
        *,
        base_configuration: TelegramRuntimeConfiguration | None,
        overrides: NavigatorAssemblyOverrides | None,
        provider: NavigatorRuntimeProvider | None,
        facade_type: type | None,
    ) -> NavigatorRuntimeProvider:
        configuration = self.configuration_resolver.resolve(
            base=base_configuration,
            facade_type=facade_type,
        )
        if configuration.facade_type is None and facade_type is not None:
            configuration = replace(configuration, facade_type=facade_type)
        factory = TelegramRuntimeProviderFactory(self.dependencies)
        return factory.create(
            configuration=configuration,
            overrides=overrides,
            provider=provider,
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
    "TelegramRuntimeConfigurationResolver",
    "TelegramRuntimeProviderFactory",
    "TelegramRuntimeBuilder",
]

"""Builders orchestrating Telegram runtime provider creation."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime import NavigatorRuntimeProvider
from navigator.contracts.runtime import NavigatorAssemblyOverrides

from .configuration import TelegramRuntimeConfiguration
from .dependencies import TelegramRuntimeDependencies
from .resolution import (
    TelegramRuntimeConfigurationResolver,
    TelegramRuntimeProviderFactory,
)


@dataclass(frozen=True)
class TelegramRuntimeBuilder:
    """Orchestrate the construction of navigator runtime providers."""

    configuration_resolver: TelegramRuntimeConfigurationResolver
    provider_factory: TelegramRuntimeProviderFactory

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
        configuration = configuration.with_facade(facade_type)
        return self.provider_factory.create(
            configuration=configuration,
            overrides=overrides,
            provider=provider,
        )


def create_runtime_builder(
    *,
    instrumentation_factory: "InstrumentationFactory" | None = None,
    runtime_resolver: "RuntimeAssemblerResolver" | None = None,
    assembly_provider: "RuntimeAssemblyProvider" | None = None,
    entrypoint: "RuntimeAssemblyEntrypoint" | None = None,
) -> TelegramRuntimeBuilder:
    """Compose a :class:`TelegramRuntimeBuilder` with resolved dependencies."""

    dependencies = TelegramRuntimeDependencies.create(
        instrumentation_factory=instrumentation_factory,
        runtime_resolver=runtime_resolver,
        assembly_provider=assembly_provider,
        entrypoint=entrypoint,
    )
    configuration_resolver = TelegramRuntimeConfigurationResolver(dependencies)
    provider_factory = TelegramRuntimeProviderFactory(dependencies)
    return TelegramRuntimeBuilder(
        configuration_resolver=configuration_resolver,
        provider_factory=provider_factory,
    )


__all__ = [
    "TelegramRuntimeBuilder",
    "create_runtime_builder",
]


if False:  # pragma: no cover - typing only
    from collections.abc import Callable, Iterable

    from navigator.contracts.runtime import NavigatorRuntimeInstrument
    from navigator.app.service.navigator_runtime import (
        RuntimeAssemblerResolver,
        RuntimeAssemblyProvider,
        RuntimeAssemblyEntrypoint,
    )

    InstrumentationFactory = Callable[[], Iterable[NavigatorRuntimeInstrument]]

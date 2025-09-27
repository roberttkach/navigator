"""Configuration resolution helpers for Telegram runtime providers."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime import (
    NavigatorRuntimeProvider,
    RuntimeAssemblyProvider,
    RuntimeAssemblerResolver,
)
from navigator.contracts.runtime import NavigatorAssemblyOverrides

from .configuration import TelegramRuntimeConfiguration
from .dependencies import TelegramRuntimeDependencies


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


__all__ = [
    "TelegramRuntimeConfigurationResolver",
    "TelegramRuntimeProviderFactory",
]


if False:  # pragma: no cover - typing only
    from navigator.app.service.navigator_runtime import NavigatorRuntimeProvider

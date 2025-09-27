"""Backwards compatible exports for Telegram runtime helpers."""
from __future__ import annotations

from navigator.app.service.navigator_runtime import (
    RuntimeAssemblerResolver,
    RuntimeAssemblyEntrypoint,
    RuntimeAssemblyProvider,
)
from navigator.contracts.runtime import NavigatorRuntimeInstrument

from .runtime import (
    TelegramAssemblyCollaborators,
    TelegramRuntimeBuilder,
    TelegramRuntimeConfiguration,
    TelegramRuntimeConfigurationResolver,
    TelegramRuntimeDependencies,
    TelegramRuntimeProviderFactory,
    TelegramInstrumentationPolicy,
    create_runtime_builder,
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
    "TelegramInstrumentationPolicy",
    "TelegramAssemblyCollaborators",
    "TelegramRuntimeDependencies",
    "TelegramRuntimeConfigurationResolver",
    "TelegramRuntimeProviderFactory",
    "TelegramRuntimeBuilder",
    "create_runtime_builder",
]

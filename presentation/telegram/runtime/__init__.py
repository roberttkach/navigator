"""Telegram presentation runtime helpers."""
from navigator.contracts.runtime import NavigatorRuntimeInstrument as NavigatorInstrument
from navigator.app.service.navigator_runtime import (
    RuntimeAssemblerResolver as RuntimeResolver,
    RuntimeAssemblyProvider as AssemblyProvider,
    RuntimeAssemblyEntrypoint as RuntimeEntrypoint,
)

from .builder import TelegramRuntimeBuilder, create_runtime_builder
from .configuration import TelegramRuntimeConfiguration, TelegramInstrumentationPolicy
from .dependencies import TelegramAssemblyCollaborators, TelegramRuntimeDependencies
from .resolution import (
    TelegramRuntimeConfigurationResolver,
    TelegramRuntimeProviderFactory,
)

__all__ = [
    "NavigatorInstrument",
    "RuntimeResolver",
    "RuntimeEntrypoint",
    "AssemblyProvider",
    "TelegramRuntimeBuilder",
    "create_runtime_builder",
    "TelegramRuntimeConfiguration",
    "TelegramInstrumentationPolicy",
    "TelegramAssemblyCollaborators",
    "TelegramRuntimeDependencies",
    "TelegramRuntimeConfigurationResolver",
    "TelegramRuntimeProviderFactory",
]

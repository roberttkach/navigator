"""Telegram-specific runtime configuration primitives."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace

from navigator.app.service.navigator_runtime import RuntimeAssemblyConfiguration, default_configuration
from navigator.contracts.runtime import NavigatorAssemblyOverrides, NavigatorRuntimeInstrument
from navigator.core.contracts import MissingAlert

from ..runtime_defaults import default_instrumentation_factory
from ..alerts import missing


@dataclass(frozen=True)
class TelegramRuntimeConfiguration:
    """Configuration bundle describing runtime assembly policies."""

    instrumentation: Sequence[NavigatorRuntimeInstrument]
    missing_alert: MissingAlert
    facade_type: type | None = None
    assembler_resolver: "RuntimeAssemblerResolver" | None = None
    provider: "RuntimeAssemblyProvider" | None = None

    @classmethod
    def create(
        cls,
        *,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
        missing_alert: MissingAlert | None = None,
        instrumentation_factory: Callable[[], Iterable[NavigatorRuntimeInstrument]] | None = None,
        facade_type: type | None = None,
        assembler_resolver: "RuntimeAssemblerResolver" | None = None,
        provider: "RuntimeAssemblyProvider" | None = None,
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

    def with_facade(self, facade_type: type | None) -> "TelegramRuntimeConfiguration":
        """Ensure that a facade type is present, preserving explicit overrides."""

        if facade_type is None or self.facade_type is not None:
            return self
        return replace(self, facade_type=facade_type)


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


__all__ = [
    "TelegramRuntimeConfiguration",
    "TelegramInstrumentationPolicy",
]


if False:  # pragma: no cover - typing only
    from navigator.app.service.navigator_runtime import RuntimeAssemblerResolver, RuntimeAssemblyProvider

"""Default dependency factories for Telegram runtime assembly."""
from __future__ import annotations

from collections.abc import Iterable

from navigator.adapters.navigator_runtime import bootstrap_runtime_assembler_resolver
from navigator.app.service.navigator_runtime import RuntimeAssemblerResolver
from navigator.contracts.runtime import NavigatorRuntimeInstrument

from .instrumentation import instrument_for_router
from .router import router as default_router


def default_instrumentation_factory() -> Iterable[NavigatorRuntimeInstrument]:
    """Return default instrumentation bound to the presentation router."""

    return (instrument_for_router(default_router),)


def default_runtime_resolver() -> RuntimeAssemblerResolver:
    """Return the bootstrap resolver used for runtime assembly."""

    return bootstrap_runtime_assembler_resolver()


__all__ = ["default_instrumentation_factory", "default_runtime_resolver"]

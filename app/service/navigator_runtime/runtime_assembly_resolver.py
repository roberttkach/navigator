"""Resolution helpers for runtime assemblers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .runtime_assembly_port import RuntimeAssemblyPort, RuntimeAssemblyRequest


class RuntimeAssemblyProvider(Protocol):
    """Provide runtime assembler implementations for the application layer."""

    def acquire(
        self,
        *,
        resolution: "ContainerResolution" | None = None,
    ) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
        """Return a runtime assembler honouring optional resolution overrides."""


@dataclass(slots=True)
class RuntimeAssemblyFactoryProvider(RuntimeAssemblyProvider):
    """Adapter turning callables into runtime assembly providers."""

    factory: Callable[["ContainerResolution" | None], RuntimeAssemblyPort[RuntimeAssemblyRequest]]

    def acquire(
        self,
        *,
        resolution: "ContainerResolution" | None = None,
    ) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
        return self.factory(resolution)


@dataclass(slots=True)
class RuntimeAssemblerResolver:
    """Resolve runtime assemblers from configured providers or overrides."""

    provider: RuntimeAssemblyProvider

    def resolve(
        self,
        *,
        assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None,
        resolution: "ContainerResolution" | None,
    ) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
        if assembler is not None:
            return assembler
        return self.provider.acquire(resolution=resolution)


def resolve_runtime_assembler(
    *,
    assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None,
    provider: RuntimeAssemblyProvider | None,
    resolution: "ContainerResolution" | None,
) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
    """Return an assembler either from explicit override or configured provider."""

    if assembler is not None:
        return assembler
    if provider is None:
        raise RuntimeError("Runtime assembler provider is not configured")
    resolver = RuntimeAssemblerResolver(provider=provider)
    return resolver.resolve(assembler=None, resolution=resolution)


__all__ = [
    "RuntimeAssemblerResolver",
    "RuntimeAssemblyFactoryProvider",
    "RuntimeAssemblyProvider",
    "resolve_runtime_assembler",
]


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - typing helpers only
        from navigator.bootstrap.navigator.container_resolution import (
            ContainerResolution,
        )

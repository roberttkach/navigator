"""Resolution helpers for runtime assemblers."""

from __future__ import annotations

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
class BootstrapRuntimeAssemblyProvider(RuntimeAssemblyProvider):
    """Bridge application assembly with the default bootstrap assembler."""

    def acquire(
        self,
        *,
        resolution: "ContainerResolution" | None = None,
    ) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
        # Import performed lazily to keep adapter coupling outside call sites.
        from navigator.adapters.navigator_runtime import BootstrapRuntimeAssembler

        return BootstrapRuntimeAssembler()


def resolve_runtime_assembler(
    *,
    assembler: RuntimeAssemblyPort[RuntimeAssemblyRequest] | None,
    provider: RuntimeAssemblyProvider | None,
    resolution: "ContainerResolution" | None,
) -> RuntimeAssemblyPort[RuntimeAssemblyRequest]:
    """Return an assembler either from explicit override or configured provider."""

    if assembler is not None:
        return assembler
    supplier = provider or BootstrapRuntimeAssemblyProvider()
    return supplier.acquire(resolution=resolution)


__all__ = [
    "BootstrapRuntimeAssemblyProvider",
    "RuntimeAssemblyProvider",
    "resolve_runtime_assembler",
]


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - typing helpers only
        from navigator.bootstrap.navigator.container_resolution import (
            ContainerResolution,
        )

"""Infrastructure helpers wiring runtime assembly providers."""
from __future__ import annotations

from navigator.app.service.navigator_runtime.runtime_assembly_resolver import (
    RuntimeAssemblerResolver,
    RuntimeAssemblyFactoryProvider,
    RuntimeAssemblyProvider,
)

from .bootstrap import BootstrapRuntimeAssembler


def bootstrap_runtime_assembly_provider() -> RuntimeAssemblyProvider:
    """Return a runtime assembly provider backed by the bootstrap assembler."""

    return RuntimeAssemblyFactoryProvider(
        factory=lambda resolution=None: BootstrapRuntimeAssembler()
    )


def bootstrap_runtime_assembler_resolver() -> RuntimeAssemblerResolver:
    """Return a resolver relying on the bootstrap runtime provider."""

    provider = bootstrap_runtime_assembly_provider()
    return RuntimeAssemblerResolver(provider=provider)


__all__ = [
    "bootstrap_runtime_assembler_resolver",
    "bootstrap_runtime_assembly_provider",
]

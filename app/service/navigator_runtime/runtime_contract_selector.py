"""Helpers responsible for selecting runtime contracts."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimeContractSelector:
    """Build contract selections isolating domain knowledge."""

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        """Return a contract selection wrapper for runtime planning."""

        return RuntimeContractSelection(usecases=usecases, contracts=contracts)


__all__ = ["RuntimeContractSelector"]

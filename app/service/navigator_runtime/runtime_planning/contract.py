"""Contract planning helpers for runtime plan construction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from ..runtime_contract_selector import RuntimeContractSelector
from ..usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimeContractPlanner:
    """Prepare contract selections for runtime plans."""

    selector: RuntimeContractSelector

    @classmethod
    def create_default(cls) -> "RuntimeContractPlanner":
        return cls(RuntimeContractSelector())

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        return self.selector.select(usecases=usecases, contracts=contracts)


class ContractPlanning(Protocol):
    """Expose a narrow contract selection capability."""

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        ...


def build_runtime_contract_selection(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    planner: ContractPlanning | None = None,
) -> RuntimeContractSelection:
    """Create the contract selection descriptor for a runtime plan."""

    candidate = planner or RuntimeContractPlanner.create_default()
    return candidate.select(usecases=usecases, contracts=contracts)


__all__ = [
    "ContractPlanning",
    "RuntimeContractPlanner",
    "build_runtime_contract_selection",
]

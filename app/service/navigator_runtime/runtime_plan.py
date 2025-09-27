"""Planning helpers describing runtime assembly inputs."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from .contracts import NavigatorRuntimeContracts, RuntimeContractSource
from .runtime_inputs import (
    RuntimeCollaboratorRequest,
    RuntimeCollaborators,
    prepare_runtime_collaborators,
)

@dataclass(frozen=True)
class RuntimeAssemblyPlan:
    """Pair resolved contracts with collaborators for runtime assembly."""

    contracts: NavigatorRuntimeContracts
    collaborators: RuntimeCollaborators


@dataclass(frozen=True)
class RuntimePlanInputs:
    """Pair resolved contracts with supporting runtime collaborators."""

    contracts: NavigatorRuntimeContracts
    collaborators: RuntimeCollaborators


@dataclass(frozen=True)
class RuntimePlanRequest:
    """Capture configuration describing how to build a runtime plan."""

    contracts: RuntimeContractSource
    collaborators: RuntimeCollaboratorRequest

    @property
    def scope(self) -> Scope:
        """Return the scope associated with the collaborator request."""

        return self.collaborators.scope


def resolve_runtime_plan_inputs(request: RuntimePlanRequest) -> RuntimePlanInputs:
    """Resolve runtime contracts and collaborators in two independent steps."""

    resolved_contracts = request.contracts.resolve()
    collaborators = prepare_runtime_collaborators(request.collaborators)
    return RuntimePlanInputs(contracts=resolved_contracts, collaborators=collaborators)


def build_runtime_plan(inputs: RuntimePlanInputs) -> RuntimeAssemblyPlan:
    """Create a runtime assembly plan from resolved inputs."""

    return RuntimeAssemblyPlan(
        contracts=inputs.contracts,
        collaborators=inputs.collaborators,
    )


def create_runtime_plan(request: RuntimePlanRequest) -> RuntimeAssemblyPlan:
    """Resolve runtime collaborators and contracts into a buildable plan."""

    inputs = resolve_runtime_plan_inputs(request)
    return build_runtime_plan(inputs)


__all__ = [
    "RuntimeAssemblyPlan",
    "RuntimePlanInputs",
    "RuntimePlanRequest",
    "build_runtime_plan",
    "create_runtime_plan",
    "resolve_runtime_plan_inputs",
]

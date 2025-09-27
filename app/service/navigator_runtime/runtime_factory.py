"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .runtime import NavigatorRuntime
from .runtime_assembler import NavigatorRuntimeAssembler
from .runtime_plan import RuntimeAssemblyPlan, RuntimePlanRequest, create_runtime_plan

from .runtime_planning import (  # re-export for backwards compatibility
    RuntimeCollaboratorPlanner,
    RuntimeContractPlanner,
    RuntimePlanRequestPlanner,
    RuntimePlannerDependencies,
    build_runtime_collaborators,
    build_runtime_contract_selection,
    create_runtime_plan_request,
)


@dataclass(frozen=True)
class NavigatorRuntimeAssembly:
    """Capture the minimal context required to assemble the runtime."""

    guard: Guardian
    plan: RuntimePlanRequest

    @property
    def scope(self) -> Scope:
        """Expose scope associated with the runtime plan."""

        return self.plan.collaborators.scope


def build_navigator_runtime(*, assembly: NavigatorRuntimeAssembly) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    plan = create_runtime_plan(assembly.plan)
    assembler = NavigatorRuntimeAssembler.from_context(
        guard=assembly.guard, scope=assembly.scope
    )
    return assembler.assemble(plan)


__all__ = [
    "NavigatorRuntimeAssembly",
    "RuntimeCollaboratorPlanner",
    "RuntimeContractPlanner",
    "RuntimePlanRequestPlanner",
    "RuntimeAssemblyPlan",
    "RuntimePlannerDependencies",
    "build_navigator_runtime",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan",
    "create_runtime_plan_request",
]

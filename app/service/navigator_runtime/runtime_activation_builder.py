"""Helpers assembling runtime instances from activation plans."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian

from .runtime import NavigatorRuntime
from .runtime_factory import NavigatorRuntimeAssembly, build_navigator_runtime
from .runtime_plan import RuntimePlanRequest


@dataclass(frozen=True)
class RuntimeActivationBuilder:
    """Convert activation requests into assembled runtime instances."""

    def build(self, *, guard: Guardian, plan: RuntimePlanRequest) -> NavigatorRuntime:
        assembly = NavigatorRuntimeAssembly(guard=guard, plan=plan)
        return build_navigator_runtime(assembly=assembly)


__all__ = ["RuntimeActivationBuilder"]

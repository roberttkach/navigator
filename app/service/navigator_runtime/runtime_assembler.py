"""Assembler coordinating runtime builder execution."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .runtime import NavigatorRuntime
from .runtime_builder import NavigatorRuntimeBuilder
from .runtime_plan import RuntimeAssemblyPlan


class NavigatorRuntimeAssembler:
    """Coordinate builder usage around a well-defined assembly plan."""

    def __init__(self, builder: NavigatorRuntimeBuilder) -> None:
        self._builder = builder

    @classmethod
    def from_context(
        cls, *, guard: Guardian, scope: Scope
    ) -> "NavigatorRuntimeAssembler":
        return cls(NavigatorRuntimeBuilder.from_context(guard=guard, scope=scope))

    def assemble(self, plan: RuntimeAssemblyPlan) -> NavigatorRuntime:
        return self._builder.assemble(plan=plan)


__all__ = ["NavigatorRuntimeAssembler"]

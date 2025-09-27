"""Incremental builder assembling navigator runtime components."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .runtime import NavigatorRuntime
from .runtime_components import RuntimeComponentBuilders
from .runtime_context import RuntimeBuildContext
from .runtime_plan import RuntimeAssemblyPlan


class NavigatorRuntimeBuilder:
    """Incrementally assemble navigator runtime components."""

    def __init__(self, builders: RuntimeComponentBuilders) -> None:
        self._builders = builders

    @classmethod
    def from_context(
        cls, *, guard: Guardian, scope: Scope
    ) -> "NavigatorRuntimeBuilder":
        context = RuntimeBuildContext(guard=guard, scope=scope)
        return cls(RuntimeComponentBuilders.for_context(context))

    def assemble(
        self,
        *,
        plan: RuntimeAssemblyPlan,
    ) -> NavigatorRuntime:
        history = self._builders.history.build_from_plan(plan)
        state = self._builders.state.build_from_plan(plan)
        tail = self._builders.tail.build_from_plan(plan)
        return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = ["NavigatorRuntimeBuilder"]

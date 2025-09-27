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
        history = plan.history.build_with(self._builders.history)
        state = plan.state.build_with(self._builders.state)
        tail = plan.tail.build_with(self._builders.tail)
        return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = ["NavigatorRuntimeBuilder"]

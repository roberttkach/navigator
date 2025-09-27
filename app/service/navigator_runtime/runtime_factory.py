"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts
from .reporter import NavigatorReporter
from .runtime import NavigatorRuntime
from .runtime_assembler import NavigatorRuntimeAssembler
from .runtime_plan import RuntimeAssemblyPlan, create_runtime_plan
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases


def build_navigator_runtime(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    scope: Scope,
    guard: Guardian,
    telemetry: Telemetry | None = None,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
    tail_telemetry: TailTelemetry | None = None,
) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    plan = create_runtime_plan(
        usecases=usecases,
        contracts=contracts,
        scope=scope,
        telemetry=telemetry,
        bundler=bundler,
        reporter=reporter,
        missing_alert=missing_alert,
        tail_telemetry=tail_telemetry,
    )
    assembler = NavigatorRuntimeAssembler.from_context(guard=guard, scope=scope)
    return assembler.assemble(plan)


__all__ = ["RuntimeAssemblyPlan", "build_navigator_runtime", "create_runtime_plan"]

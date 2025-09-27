"""Planning helpers describing runtime assembly inputs."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts
from .reporter import NavigatorReporter
from .runtime_inputs import (
    RuntimeCollaborators,
    prepare_runtime_collaborators,
    resolve_runtime_contracts,
)
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimeAssemblyPlan:
    """Describe the collaborators required to assemble the runtime."""

    contracts: NavigatorRuntimeContracts
    collaborators: RuntimeCollaborators


def create_runtime_plan(
    *,
    usecases: NavigatorUseCases | None,
    contracts: NavigatorRuntimeContracts | None,
    scope: Scope,
    telemetry: Telemetry | None,
    bundler: PayloadBundler | None,
    reporter: NavigatorReporter | None,
    missing_alert: MissingAlert | None,
    tail_telemetry: TailTelemetry | None,
) -> RuntimeAssemblyPlan:
    """Resolve runtime collaborators and contracts into a buildable plan."""

    resolved_contracts = resolve_runtime_contracts(
        usecases=usecases, contracts=contracts
    )
    collaborators = prepare_runtime_collaborators(
        scope=scope,
        telemetry=telemetry,
        reporter=reporter,
        bundler=bundler,
        tail_telemetry=tail_telemetry,
        missing_alert=missing_alert,
    )
    return RuntimeAssemblyPlan(
        contracts=resolved_contracts,
        collaborators=collaborators,
    )


__all__ = ["RuntimeAssemblyPlan", "create_runtime_plan"]

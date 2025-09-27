"""Helpers resolving runtime inputs before assembly."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts
from .reporter import NavigatorReporter
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimeCollaborators:
    """Resolved cross-cutting collaborators used by the runtime."""

    bundler: PayloadBundler
    reporter: NavigatorReporter
    telemetry: Telemetry | None
    tail_telemetry: TailTelemetry | None
    missing_alert: MissingAlert | None


def resolve_runtime_contracts(
    *,
    usecases: NavigatorUseCases | None,
    contracts: NavigatorRuntimeContracts | None,
) -> NavigatorRuntimeContracts:
    """Derive runtime contracts from use cases when not provided explicitly."""

    if contracts is not None:
        return contracts
    if usecases is None:
        raise ValueError("either usecases or contracts must be provided")
    return NavigatorRuntimeContracts.from_usecases(usecases)


def provide_payload_bundler(bundler: PayloadBundler | None) -> PayloadBundler:
    """Return a payload bundler, instantiating a default one when missing."""

    return bundler or PayloadBundler()


def provide_runtime_reporter(
    scope: Scope,
    telemetry: Telemetry | None,
    reporter: NavigatorReporter | None,
) -> NavigatorReporter:
    """Resolve telemetry reporter used by runtime services."""

    if reporter is not None:
        return reporter
    if telemetry is None:
        raise ValueError("telemetry must be provided when reporter is not supplied")
    return NavigatorReporter(telemetry, scope)


def ensure_runtime_telemetry(
    telemetry: Telemetry | None, tail_telemetry: TailTelemetry | None
) -> None:
    """Validate that runtime assembly receives at least one telemetry entry."""

    if telemetry is None and tail_telemetry is None:
        raise ValueError("either telemetry or tail_telemetry must be provided")


def prepare_runtime_collaborators(
    *,
    scope: Scope,
    telemetry: Telemetry | None,
    reporter: NavigatorReporter | None,
    bundler: PayloadBundler | None,
    tail_telemetry: TailTelemetry | None,
    missing_alert: MissingAlert | None,
) -> RuntimeCollaborators:
    """Resolve runtime collaborators and ensure telemetry prerequisites."""

    resolved_bundler = provide_payload_bundler(bundler)
    resolved_reporter = provide_runtime_reporter(scope, telemetry, reporter)
    ensure_runtime_telemetry(telemetry, tail_telemetry)
    return RuntimeCollaborators(
        bundler=resolved_bundler,
        reporter=resolved_reporter,
        telemetry=telemetry,
        tail_telemetry=tail_telemetry,
        missing_alert=missing_alert,
    )


__all__ = [
    "RuntimeCollaborators",
    "ensure_runtime_telemetry",
    "prepare_runtime_collaborators",
    "provide_payload_bundler",
    "provide_runtime_reporter",
    "resolve_runtime_contracts",
]

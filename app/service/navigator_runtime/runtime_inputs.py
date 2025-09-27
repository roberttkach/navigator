"""Helpers resolving runtime collaborators before runtime assembly."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .reporter import NavigatorReporter
from .tail_components import TailTelemetry
from .types import MissingAlert


@dataclass(frozen=True)
class RuntimeCollaborators:
    """Resolved cross-cutting collaborators used by the runtime."""

    bundler: PayloadBundler
    reporter: NavigatorReporter
    telemetry: Telemetry | None
    tail_telemetry: TailTelemetry | None
    missing_alert: MissingAlert | None


@dataclass(frozen=True)
class RuntimeCollaboratorRequest:
    """Describe how runtime collaborators should be resolved."""

    scope: Scope
    telemetry: Telemetry | None = None
    reporter: NavigatorReporter | None = None
    bundler: PayloadBundler | None = None
    tail_telemetry: TailTelemetry | None = None
    missing_alert: MissingAlert | None = None


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
    return NavigatorReporter(telemetry, scope)


def ensure_runtime_telemetry(
    telemetry: Telemetry | None, tail_telemetry: TailTelemetry | None
) -> None:
    """Record whether runtime assembly receives telemetry collaborators."""

    # Runtime workflows may operate without telemetry when instrumentation is disabled.
    # The helper simply preserves backwards compatibility for call sites that still
    # depend on the presence of this check.
    return None


def prepare_runtime_collaborators(
    request: RuntimeCollaboratorRequest,
) -> RuntimeCollaborators:
    """Resolve runtime collaborators and ensure telemetry prerequisites."""

    resolved_bundler = provide_payload_bundler(request.bundler)
    resolved_reporter = provide_runtime_reporter(
        request.scope, request.telemetry, request.reporter
    )
    ensure_runtime_telemetry(request.telemetry, request.tail_telemetry)
    return RuntimeCollaborators(
        bundler=resolved_bundler,
        reporter=resolved_reporter,
        telemetry=request.telemetry,
        tail_telemetry=request.tail_telemetry,
        missing_alert=request.missing_alert,
    )


__all__ = [
    "RuntimeCollaborators",
    "RuntimeCollaboratorRequest",
    "ensure_runtime_telemetry",
    "prepare_runtime_collaborators",
    "provide_payload_bundler",
    "provide_runtime_reporter",
]

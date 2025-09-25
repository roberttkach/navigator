"""Define telemetry trace specifications for async workflows."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.telemetry import LogCode


@dataclass(frozen=True, slots=True)
class TraceSpec:
    """Immutable contract describing telemetry codes for traced operations."""

    begin: LogCode
    success: LogCode
    failure: LogCode


def _render_spec(success: LogCode) -> TraceSpec:
    """Create a trace specification with render start and skip fallback."""

    return TraceSpec(LogCode.RENDER_START, success, LogCode.RENDER_SKIP)


APPEND = _render_spec(LogCode.RENDER_OK)
REPLACE = _render_spec(LogCode.RENDER_OK)
SET = _render_spec(LogCode.RENDER_OK)
BACK = _render_spec(LogCode.RENDER_OK)
REBASE = _render_spec(LogCode.REBASE_SUCCESS)
POP = _render_spec(LogCode.POP_SUCCESS)

__all__ = [
    "TraceSpec",
    "APPEND",
    "REPLACE",
    "SET",
    "BACK",
    "REBASE",
    "POP",
]

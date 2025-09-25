"""Telemetry trace specifications for application use-cases."""
from __future__ import annotations

from dataclasses import dataclass

from ...core.telemetry import LogCode


@dataclass(frozen=True, slots=True)
class TraceSpec:
    """Immutable contract describing telemetry codes for traced operations."""

    begin: LogCode
    success: LogCode
    failure: LogCode


APPEND = TraceSpec(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
REPLACE = TraceSpec(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
SET = TraceSpec(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
BACK = TraceSpec(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
REBASE = TraceSpec(LogCode.RENDER_START, LogCode.REBASE_SUCCESS, LogCode.RENDER_SKIP)
POP = TraceSpec(LogCode.RENDER_START, LogCode.POP_SUCCESS, LogCode.RENDER_SKIP)

__all__ = [
    "TraceSpec",
    "APPEND",
    "REPLACE",
    "SET",
    "BACK",
    "REBASE",
    "POP",
]

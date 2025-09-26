"""Common utilities shared across manual scenarios."""
from __future__ import annotations

from contextlib import asynccontextmanager

from navigator.core.telemetry import Telemetry


class _StubTelemetryPort:
    def calibrate(self, mode: str) -> None:  # pragma: no cover - manual helper
        return None

    def emit(self, code, level, *, origin=None, **fields) -> None:  # pragma: no cover
        return None


def monitor() -> Telemetry:
    """Return a telemetry instance backed by a no-op port."""

    return Telemetry(_StubTelemetryPort())


@asynccontextmanager
async def sentinel():
    """Async context manager used in manual scenarios."""

    yield


__all__ = ["monitor", "sentinel"]

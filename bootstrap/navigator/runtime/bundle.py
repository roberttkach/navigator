"""Represent the resulting navigator runtime bundle."""
from __future__ import annotations

from dataclasses import dataclass
from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.core.telemetry import Telemetry

from ..container_types import RuntimeContainer


@dataclass(frozen=True)
class NavigatorRuntimeBundle:
    """Aggregate runtime services exposed to bootstrap instrumentation."""

    telemetry: Telemetry
    container: RuntimeContainer
    runtime: NavigatorRuntime


__all__ = ["NavigatorRuntimeBundle"]

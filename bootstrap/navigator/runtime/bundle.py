"""Represent the resulting navigator runtime bundle."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer


@dataclass(frozen=True)
class NavigatorRuntimeBundle:
    """Aggregate runtime services exposed to bootstrap instrumentation."""

    telemetry: Telemetry
    container: AppContainer
    runtime: NavigatorRuntime


__all__ = ["NavigatorRuntimeBundle"]

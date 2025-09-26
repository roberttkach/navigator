"""Represent the resulting navigator runtime bundle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from navigator.app.service.navigator_runtime import NavigatorRuntime
from navigator.core.telemetry import Telemetry

if TYPE_CHECKING:
    from navigator.infra.di.container import AppContainer


@dataclass(frozen=True)
class NavigatorRuntimeBundle:
    """Aggregate runtime services exposed to bootstrap instrumentation."""

    telemetry: Telemetry
    container: "AppContainer"
    runtime: NavigatorRuntime


__all__ = ["NavigatorRuntimeBundle"]

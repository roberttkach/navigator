"""Definitions for navigator runtime dependency bundles."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from .types import MissingAlert
from .usecases import NavigatorUseCases
from navigator.core.telemetry import Telemetry


@dataclass(frozen=True)
class NavigatorDependencies:
    """Minimal set of services required to assemble a navigator runtime."""

    usecases: NavigatorUseCases
    guard: Guardian
    telemetry: Telemetry
    missing_alert: MissingAlert


__all__ = ["NavigatorDependencies"]

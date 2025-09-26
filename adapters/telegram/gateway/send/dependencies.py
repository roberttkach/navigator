"""Dependency bundles supporting Telegram send operations."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.telemetry import Telemetry

from ..serializer.screen import SignatureScreen


@dataclass(frozen=True)
class SendDependencies:
    """Bundle dependencies used by send handlers."""

    schema: ExtraSchema
    screen: SignatureScreen
    policy: MediaPathPolicy
    limits: Limits
    telemetry: Telemetry


__all__ = ["SendDependencies"]

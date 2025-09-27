"""Telemetry helpers dedicated to navigator tail operations."""
from __future__ import annotations

import logging

from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

from .edit_request import TailEditDescription


class TailTelemetry:
    """Emit structured telemetry for navigator tail operations."""

    def __init__(self, channel: TelemetryChannel, *, scope: Scope) -> None:
        self._channel = channel
        self._profile = profile(scope)

    @classmethod
    def from_telemetry(cls, telemetry: Telemetry, scope: Scope) -> "TailTelemetry":
        channel = telemetry.channel(__name__)
        return cls(channel, scope=scope)

    def emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )

    def record_get(self) -> None:
        """Record the retrieval of the last navigator message."""

        self.emit("last.get")

    def record_delete(self) -> None:
        """Record deletion of the last navigator message."""

        self.emit("last.delete")

    def record_edit(self, description: TailEditDescription) -> None:
        """Record metadata about an edit applied to the navigator tail."""

        self.emit(
            "last.edit",
            payload={
                "text": description.text,
                "media": description.media,
                "group": description.group,
            },
        )


__all__ = ["TailTelemetry"]

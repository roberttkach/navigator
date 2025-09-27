"""Telemetry observers for add-use-case history interactions."""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class AppendHistoryObserver(Protocol):
    """Protocol describing side effects performed during append access."""

    def history_loaded(self, scope: Scope, count: int) -> None: ...

    def state_retrieved(self, status: Optional[str]) -> None: ...


class NullAppendHistoryObserver:
    """No-op implementation shielding access from optional observers."""

    def history_loaded(self, scope: Scope, count: int) -> None:  # pragma: no cover - no-op
        return

    def state_retrieved(self, status: Optional[str]) -> None:  # pragma: no cover - no-op
        return


class AppendHistoryJournal(AppendHistoryObserver):
    """Emit telemetry envelopes for append history events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history")

    def history_loaded(self, scope: Scope, count: int) -> None:
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": count},
            scope=profile(scope),
        )

    def state_retrieved(self, status: Optional[str]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_GET,
            op="add",
            state={"current": status},
        )


__all__ = [
    "AppendHistoryJournal",
    "AppendHistoryObserver",
    "NullAppendHistoryObserver",
]


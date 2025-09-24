from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


@dataclass(slots=True)
class TimeCodec:
    telemetry: Telemetry | None = None

    def __post_init__(self) -> None:
        self._channel: TelemetryChannel | None = (
            self.telemetry.channel(__name__) if self.telemetry else None
        )

    def _emit(self, level: int, *, raw: Any) -> None:
        if self._channel:
            preview = raw[:64] if isinstance(raw, str) else (str(raw)[:64] if raw is not None else None)
            self._channel.emit(level, LogCode.HISTORY_LOAD, note="history_message_invalid_ts", raw=preview)

    @staticmethod
    def pack(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def unpack(self, raw: Any) -> datetime:
        if isinstance(raw, str):
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if getattr(dt, "tzinfo", None):
                    return dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=timezone.utc)
            except Exception as exc:  # pragma: no cover - defensive
                self._emit(logging.ERROR, raw=raw)
                raise ValueError(f"History message payload has invalid 'ts': {raw!r}") from exc
        self._emit(logging.ERROR, raw=raw)
        raise ValueError(
            "History message payload has invalid 'ts': "
            f"{raw!r} (type {type(raw).__name__})"
        )


__all__ = ["TimeCodec"]

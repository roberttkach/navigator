from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from navigator.core.telemetry import LogCode, telemetry

channel = telemetry.channel(__name__)


class TimeCodec:
    @staticmethod
    def pack(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def unpack(raw: Any) -> datetime:
        if isinstance(raw, str):
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if getattr(dt, "tzinfo", None):
                    return dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=timezone.utc)
            except Exception as exc:  # pragma: no cover - defensive
                channel.emit(
                    logging.ERROR,
                    LogCode.HISTORY_LOAD,
                    note="history_message_invalid_ts",
                    raw=raw[:64],
                )
                raise ValueError(f"History message payload has invalid 'ts': {raw!r}") from exc
        channel.emit(
            logging.ERROR,
            LogCode.HISTORY_LOAD,
            note="history_message_invalid_ts",
            raw=(str(raw)[:64] if raw is not None else None),
        )
        raise ValueError(
            "History message payload has invalid 'ts': "
            f"{raw!r} (type {type(raw).__name__})"
        )


__all__ = ["TimeCodec"]

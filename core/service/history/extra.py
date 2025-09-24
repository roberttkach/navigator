"""Utilities for sanitizing history message extras before persistence."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ...telemetry import LogCode, Telemetry, TelemetryChannel
from ...util.entities import sanitize


def cleanse(
    extra: Any,
    *,
    length: int,
    telemetry: Telemetry | None = None,
) -> Optional[Dict[str, Any]]:
    """Normalize a history ``extra`` payload into a JSON-friendly mapping."""

    if not isinstance(extra, dict):
        return None

    filtered: Dict[str, Any] = {}
    channel: TelemetryChannel | None = (
        telemetry.channel(__name__) if telemetry else None
    )

    for key, value in extra.items():
        if key == "entities":
            vetted = sanitize(value, length, telemetry=telemetry)
            if vetted:
                filtered["entities"] = vetted
            elif channel:
                channel.emit(
                    logging.DEBUG,
                    LogCode.EXTRA_UNKNOWN_DROPPED,
                    filtered_keys=["entities"],
                )
            continue

        if key == "thumb" and value is not None:
            filtered["has_thumb"] = True
            continue

        filtered[key] = value

    return filtered or None


__all__ = ["cleanse"]

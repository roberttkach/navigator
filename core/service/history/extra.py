"""Utilities for sanitizing history message extras before persistence."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ...telemetry import LogCode, telemetry
from ...util.entities import sanitize

channel = telemetry.channel(__name__)


def cleanse(extra: Any, *, length: int) -> Optional[Dict[str, Any]]:
    """Normalize a history ``extra`` payload into a JSON-friendly mapping."""

    if not isinstance(extra, dict):
        return None

    filtered: Dict[str, Any] = {}

    for key, value in extra.items():
        if key == "entities":
            vetted = sanitize(value, length)
            if vetted:
                filtered["entities"] = vetted
            else:
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

"""Support lightweight classification and comparison of payload metadata."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Dict

from ...entity.markup import Markup
from ...value.content import Payload


def classify(payload: Payload) -> Dict[str, Any]:
    """Describe the payload family to drive downstream rendering choices."""

    if payload.group:
        return {"kind": "group", "group_len": len(payload.group)}
    if payload.media:
        medium = getattr(payload.media.type, "value", None)
        return {"kind": "media", "medium": medium}
    return {"kind": "text"}


def _canonicalize(data: object) -> str | None:
    """Serialize mapping-like objects into a canonical JSON snapshot."""

    if not isinstance(data, Mapping):
        return None
    return json.dumps(dict(data), sort_keys=True, separators=(",", ":"))


def match(first: Markup | None, second: Markup | None) -> bool:
    """Check whether markups share the same structural intent."""

    if first is None and second is None:
        return True
    if (first is None) != (second is None):
        return False
    return (
        getattr(first, "kind", None) == getattr(second, "kind", None)
        and _canonicalize(getattr(first, "data", None))
        == _canonicalize(getattr(second, "data", None))
    )

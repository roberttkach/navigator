import json
from typing import Dict, Any

from ...entity.markup import Markup
from ...value.content import Payload


def payload_kind(p: Payload) -> Dict[str, Any]:
    if p.group:
        return {"kind": "group", "group_len": len(p.group)}
    if p.media:
        return {"kind": "media", "media_type": getattr(p.media.type, "value", None)}
    return {"kind": "text"}


def _canon(d):  # noqa: ANN001
    return json.dumps(d, sort_keys=True, separators=(",", ":")) if isinstance(d, dict) else None


def reply_equal(a: Markup | None, b: Markup | None) -> bool:
    if a is None and b is None:
        return True
    if (a is None) != (b is None):
        return False
    return (
            getattr(a, "kind", None) == getattr(b, "kind", None)
            and _canon(getattr(a, "data", None)) == _canon(getattr(b, "data", None))
    )

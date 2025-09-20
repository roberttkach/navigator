from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from ...logging.code import LogCode

REDACT_KEYS = {"path", "inline_id", "biz_id", "url", "caption", "thumb"}
# Режимы:
# - debug: без редактирования;
# - safe (по умолчанию): редактируются ключи из REDACT_KEYS;
# - paranoid: дополнительно редактируются text и entities.
REDACTION_MODE = os.getenv("NAV_LOG_REDACTION", "safe").lower()


def _keys_to_redact() -> set[str]:
    base = set(REDACT_KEYS)
    if REDACTION_MODE == "paranoid":
        base.update({"text", "entities"})
    return base


def _redact(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, dict):
        keys = _keys_to_redact()
        return {
            k: ("***" if k in keys and REDACTION_MODE != "debug" else _redact(vv))
            for k, vv in v.items()
        }
    if isinstance(v, (list, tuple)):
        return [_redact(x) for x in v]
    return v


def jlog(logger: logging.Logger, level: int, code: LogCode, **fields: Any) -> None:
    if not logger.isEnabledFor(level):
        return
    redacted_fields = _redact(dict(fields))
    exc_info = bool(redacted_fields.pop("exc_info", False))
    payload: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "code": code.value,
        **redacted_fields,
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str), exc_info=exc_info)

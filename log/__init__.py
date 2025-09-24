from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

REDACT_KEYS = {"path", "inline", "business", "url", "caption", "thumb"}
DEFAULT_MODE = "safe"
_mode = DEFAULT_MODE


class LogCode(Enum):
    # Render / Rerender
    RENDER_START = "render_start"
    RENDER_OK = "render_ok"
    RENDER_SKIP = "render_skip"
    RERENDER_START = "rerender_start"
    RERENDER_INLINE_NO_FALLBACK = "rerender_inline_no_fallback"

    # Inline
    INLINE_CONTENT_SWITCH_FORBIDDEN = "inline_content_switch_forbidden"
    INLINE_REMAP_DELETE_SEND = "inline_remap_delete_send"

    # Albums
    ALBUM_PARTIAL_OK = "album_partial_ok"
    ALBUM_PARTIAL_FALLBACK = "album_partial_fallback"

    # History / Last / State
    HISTORY_LOAD = "history_load"
    HISTORY_SAVE = "history_save"
    HISTORY_TRIM = "history_trim"
    LAST_GET = "last_get"
    LAST_SET = "last_set"
    LAST_DELETE = "last_delete"
    STATE_GET = "state_get"
    STATE_SET = "state_set"
    STATE_DATA_GET = "state_data_get"

    # Registry / Navigator / Router
    REGISTRY_REGISTER = "registry_register"
    REGISTRY_GET = "registry_get"
    REGISTRY_HAS = "registry_has"
    NAVIGATOR_API = "navigator_api"
    ROUTER_BACK_ENTER = "router_back_enter"
    ROUTER_BACK_DONE = "router_back_done"
    ROUTER_BACK_FAIL = "router_back_fail"

    # Gateway
    GATEWAY_SEND_OK = "gateway_send_ok"
    GATEWAY_SEND_FAIL = "gateway_send_fail"
    GATEWAY_EDIT_OK = "gateway_edit_ok"
    GATEWAY_EDIT_FAIL = "gateway_edit_fail"
    GATEWAY_DELETE_OK = "gateway_delete_ok"
    GATEWAY_DELETE_FAIL = "gateway_delete_fail"
    GATEWAY_NOTIFY_EMPTY = "gateway_notify_empty"
    GATEWAY_NOTIFY_OK = "gateway_notify_ok"
    TELEGRAM_RETRY = "telegram_retry"
    TELEGRAM_UNHANDLED_ERROR = "telegram_unhandled_error"

    # Extras / Serializer
    EXTRA_FILTERED_OUT = "extra_filtered_out"
    EXTRA_UNKNOWN_DROPPED = "extra_unknown_dropped"
    EXTRA_EFFECT_STRIPPED = "extra_effect_stripped"
    MARKUP_ENCODE = "markup_encode"
    MARKUP_DECODE = "markup_decode"

    # Media / Limits
    MEDIA_UNSUPPORTED = "media_unsupported"
    TOO_LONG_TRUNCATED = "too_long_truncated"

    # Ops
    POP_SUCCESS = "pop_success"
    REBASE_SUCCESS = "rebase_success"
    RESTORE_DYNAMIC = "restore_dynamic"
    RESTORE_DYNAMIC_FALLBACK = "restore_dynamic_fallback"


def calibrate(mode: str) -> None:
    """Configure log redaction mode."""

    global _mode
    normal = (mode or DEFAULT_MODE).lower()
    if normal not in {"debug", "safe", "paranoid"}:
        normal = DEFAULT_MODE
    _mode = normal


def _targets() -> set[str]:
    base = set(REDACT_KEYS)
    if _mode == "paranoid":
        base.update({"text", "entities"})
    return base


def _filter(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        keys = _targets()
        return {
            key: ("***" if key in keys and _mode != "debug" else _filter(inner))
            for key, inner in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_filter(item) for item in value]
    return value


def jlog(logger: logging.Logger, level: int, code: LogCode, **fields: Any) -> None:
    if not logger.isEnabledFor(level):
        return
    scrubbed = _filter(dict(fields))
    trace = bool(scrubbed.pop("exc_info", False))
    payload: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "code": code.value,
        **scrubbed,
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str), exc_info=trace)


__all__ = ["LogCode", "calibrate", "jlog"]

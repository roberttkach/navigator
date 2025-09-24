from __future__ import annotations

import inspect
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from ...core.telemetry import LogCode, telemetry


def _capture(fn: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[Optional[dict], Optional[dict]]:
    signature = inspect.signature(fn)
    binding = signature.bind_partial(*args, **kwargs)
    scope = binding.arguments.get("scope")
    payload = binding.arguments.get("payload")
    try:
        from ...core.service.scope import profile

        scope = profile(scope) if scope is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):
        scope = None
    try:
        from ...core.service.rendering.helpers import classify

        payload = classify(payload) if payload is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):
        payload = None
    return scope, payload


def _snapshot(result: Any) -> Optional[dict]:
    identifier = getattr(result, "id", None)
    extra = getattr(result, "extra", None)
    if identifier is None and extra is None:
        return None
    return {"id": identifier, "extra_len": len(extra) if isinstance(extra, list) else 0}


def trace(begin, success, skip, augment: Optional[Callable[[Any], dict]] = None):
    def deco(fn: Callable[..., Any]):
        channel = telemetry.channel(fn.__module__)

        @wraps(fn)
        async def decorated(*args, **kwargs):
            scope, payload = _capture(fn, args, kwargs)
            channel.emit(logging.INFO, begin, scope=scope, payload=payload)
            started = time.monotonic()
            try:
                result = await fn(*args, **kwargs)
            except Exception:
                channel.emit(logging.WARNING, skip, scope=scope, payload=payload, exc_info=True)
                raise
            elapsed = time.monotonic() - started
            meta = augment(result) if augment else _snapshot(result)
            channel.emit(logging.INFO, success, scope=scope, payload=payload, elapsed=elapsed, result=meta)
            return result

        return decorated

    return deco


__all__ = ["trace"]

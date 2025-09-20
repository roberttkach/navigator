import inspect
import logging
from functools import wraps
from time import perf_counter
from typing import Any, Optional, Callable, Tuple, Dict

from .emit import jlog


def _extract_scope_payload(fn: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[
    Optional[dict], Optional[dict]]:
    sig = inspect.signature(fn)
    ba = sig.bind_partial(*args, **kwargs)
    scope = ba.arguments.get("scope")
    payload = ba.arguments.get("payload")
    try:
        from ...domain.service.scope import profile
        scope_val = profile(scope) if scope is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):
        scope_val = None
    try:
        from ...domain.service.rendering.helpers import payload_kind
        payload_val = payload_kind(payload) if payload is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):
        payload_val = None
    return scope_val, payload_val


def _message_summary(result: Any) -> Optional[dict]:
    mid = getattr(result, "id", None)
    extra = getattr(result, "extra", None)
    if mid is None and extra is None:
        return None
    return {"id": mid, "extra_len": len(extra) if isinstance(extra, list) else 0}


def log_io(code_start, code_ok, code_skip, extra_fn: Optional[Callable[[Any], dict]] = None):
    def deco(fn: Callable[..., Any]):
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            module_name = getattr(fn, "__module__", __name__)
            logger = logging.getLogger(module_name)
            start = perf_counter()
            scope_val, payload_val = _extract_scope_payload(fn, args, kwargs)
            if code_start is not None:
                fields: Dict[str, Any] = {}
                if scope_val is not None:
                    fields["scope"] = scope_val
                if payload_val is not None:
                    fields["payload"] = payload_val
                jlog(logger, logging.INFO, code_start, **fields)
            result = await fn(*args, **kwargs)
            dur = int((perf_counter() - start) * 1000)
            if code_ok is not None or code_skip is not None:
                fields: Dict[str, Any] = {"duration_ms": dur}
                if scope_val is not None:
                    fields["scope"] = scope_val
                if payload_val is not None:
                    fields["payload"] = payload_val
                if result is None:
                    if code_skip is not None:
                        jlog(logger, logging.INFO, code_skip, **fields)
                else:
                    if code_ok is not None:
                        msg = _message_summary(result)
                        if msg is not None:
                            fields["message"] = msg
                        if extra_fn is not None:
                            try:
                                extra = extra_fn(result)
                                if isinstance(extra, dict):
                                    fields.update(extra)
                            except (TypeError, ValueError):
                                pass
                        jlog(logger, logging.INFO, code_ok, **fields)
            return result

        return wrapper

    return deco

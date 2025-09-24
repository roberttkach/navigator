import inspect
import logging
from functools import wraps
import inspect
import logging
import time
from typing import Any, Optional, Callable, Tuple, Dict

from ...core.telemetry import LogCode, telemetry


def _capture(fn: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[
    Optional[dict], Optional[dict]]:
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
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            module = getattr(fn, "__module__", __name__)
            channel = telemetry.channel(module)
            start = time.perf_counter()
            scope, payload = _capture(fn, args, kwargs)
            if begin is not None:
                fields: Dict[str, Any] = {}
                if scope is not None:
                    fields["scope"] = scope
                if payload is not None:
                    fields["payload"] = payload
                channel.emit(logging.INFO, begin, **fields)
            result = await fn(*args, **kwargs)
            duration = int((time.perf_counter() - start) * 1000)
            if success is not None or skip is not None:
                fields: Dict[str, Any] = {"duration_ms": duration}
                if scope is not None:
                    fields["scope"] = scope
                if payload is not None:
                    fields["payload"] = payload
                if result is None:
                    if skip is not None:
                        channel.emit(logging.INFO, skip, **fields)
                else:
                    if success is not None:
                        summary = _snapshot(result)
                        if summary is not None:
                            fields["message"] = summary
                        if augment is not None:
                            try:
                                extra = augment(result)
                                if isinstance(extra, dict):
                                    fields.update(extra)
                            except (TypeError, ValueError):
                                pass
                        channel.emit(logging.INFO, success, **fields)
            return result

        return wrapper

    return deco

"""Reusable telemetry instrumentation helpers for application services."""
from __future__ import annotations

import inspect
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from ...core.telemetry import Telemetry
from .events import TraceSpec


def _capture(
    fn: Callable[..., Any],
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Tuple[Optional[dict], Optional[dict]]:
    signature = inspect.signature(fn)
    binding = signature.bind_partial(*args, **kwargs)
    scope = binding.arguments.get("scope")
    payload = binding.arguments.get("payload")
    try:
        from ...core.service.scope import profile

        scope = profile(scope) if scope is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):  # pragma: no cover - defensive
        scope = None
    try:
        from ...core.service.rendering.helpers import classify

        payload = classify(payload) if payload is not None else None
    except (AttributeError, ImportError, TypeError, ValueError):  # pragma: no cover - defensive
        payload = None
    return scope, payload


def _snapshot(result: Any) -> Optional[dict]:
    identifier = getattr(result, "id", None)
    extra = getattr(result, "extra", None)
    if identifier is None and extra is None:
        return None
    return {"id": identifier, "extra_len": len(extra) if isinstance(extra, list) else 0}


class TraceAspect:
    """Helper responsible for emitting begin/success/failure telemetry envelopes."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._telemetry = telemetry

    async def run(
        self,
        spec: TraceSpec,
        call: Callable[..., Awaitable[Any]],
        *args: Any,
        augment: Callable[[Any], Optional[dict]] | None = None,
        **kwargs: Any,
    ) -> Any:
        channel = self._telemetry.channel(call.__module__)
        scope, payload = _capture(call, args, kwargs)
        channel.emit(logging.INFO, spec.begin, scope=scope, payload=payload)
        started = time.monotonic()
        try:
            result = await call(*args, **kwargs)
        except Exception:
            channel.emit(
                logging.WARNING,
                spec.failure,
                scope=scope,
                payload=payload,
                exc_info=True,
            )
            raise
        elapsed = time.monotonic() - started
        meta = augment(result) if augment else _snapshot(result)
        channel.emit(
            logging.INFO,
            spec.success,
            scope=scope,
            payload=payload,
            elapsed=elapsed,
            result=meta,
        )
        return result


__all__ = ["TraceAspect"]

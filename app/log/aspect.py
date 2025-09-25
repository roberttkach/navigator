"""Emit trace envelopes around asynchronous operations."""

from __future__ import annotations

import inspect
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .events import TraceSpec
from ...core.service.rendering.helpers import classify
from ...core.service.scope import profile
from ...core.telemetry import Telemetry

Capture = Tuple[Optional[dict], Optional[dict]]


def _capture_context(
        fn: Callable[..., Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
) -> Capture:
    """Extract stable telemetry context from ``fn`` call arguments."""

    signature = inspect.signature(fn)
    binding = signature.bind_partial(*args, **kwargs)
    scope = binding.arguments.get("scope")
    payload = binding.arguments.get("payload")
    scoped = profile(scope) if scope is not None else None
    classified = classify(payload) if payload is not None else None
    return scoped, classified


def _snapshot(result: Any) -> Optional[dict]:
    """Return lightweight telemetry metadata extracted from ``result``."""

    identifier = getattr(result, "id", None)
    extra = getattr(result, "extra", None)
    if identifier is None and extra is None:
        return None
    return {"id": identifier, "extra_len": len(extra) if isinstance(extra, list) else 0}


class TraceAspect:
    """Coordinate begin/success/failure telemetry around async calls."""

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
        """Run ``call`` while reporting progress through ``spec`` telemetry."""

        channel = self._telemetry.channel(call.__module__)
        scope, payload = _capture_context(call, args, kwargs)
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

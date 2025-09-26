"""Capture reusable telemetry helpers for traced async operations."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .events import TraceSpec
from ...core.service.rendering.helpers import classify
from ...core.service.scope import profile
from ...core.telemetry import Telemetry
from ...core.value.content import Payload
from ...core.value.message import Scope


@dataclass(frozen=True, slots=True)
class TraceContext:
    """Describe the scope and payload extracted for telemetry."""

    scope: Optional[dict]
    payload: Optional[dict]


def _capture_context(
        fn: Callable[..., Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
) -> TraceContext:
    """Extract stable telemetry context from ``fn`` call arguments."""

    del fn  # function identity is irrelevant for structural context capture
    values = list(args) + list(kwargs.values())
    scope = _extract_scope(values)
    payload = _extract_payload(values)
    scoped = profile(scope) if scope is not None else None
    classified = _classify_payload(payload) if payload is not None else None
    return TraceContext(scope=scoped, payload=classified)


def _extract_scope(values: Sequence[Any]) -> Scope | None:
    """Return the first :class:`Scope` instance from ``values`` if any."""

    for value in values:
        if isinstance(value, Scope):
            return value
    return None


def _extract_payload(values: Sequence[Any]) -> Payload | Sequence[Payload] | None:
    """Return payload artefacts discovered inside ``values``."""

    for value in values:
        if isinstance(value, Payload):
            return value
        if _is_payload_sequence(value):
            return value
    return None


def _is_payload_sequence(candidate: Any) -> bool:
    """Check whether ``candidate`` looks like a payload sequence."""

    if isinstance(candidate, (str, bytes)):
        return False
    if isinstance(candidate, Sequence):
        return any(isinstance(item, Payload) for item in candidate)
    return False


def _classify_payload(payload: Payload | Sequence[Payload]) -> Optional[dict]:
    """Convert payload artefacts into lightweight telemetry metadata."""

    if isinstance(payload, Payload):
        return classify(payload)
    items = [item for item in payload if isinstance(item, Payload)]
    if not items:
        return None
    if len(items) == 1:
        return classify(items[0])
    families: Dict[str, int] = {}
    for item in items:
        kind = classify(item).get("kind", "unknown")
        families[kind] = families.get(kind, 0) + 1
    return {"kind": "bundle", "size": len(items), "families": families}


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
        context = _capture_context(call, args, kwargs)
        channel.emit(logging.INFO, spec.begin, scope=context.scope, payload=context.payload)
        started = time.monotonic()
        try:
            result = await call(*args, **kwargs)
        except Exception:
            channel.emit(
                logging.WARNING,
                spec.failure,
                scope=context.scope,
                payload=context.payload,
                exc_info=True,
            )
            raise
        elapsed = time.monotonic() - started
        meta = augment(result) if augment else _snapshot(result)
        channel.emit(
            logging.INFO,
            spec.success,
            scope=context.scope,
            payload=context.payload,
            elapsed=elapsed,
            result=meta,
        )
        return result


__all__ = ["TraceAspect"]

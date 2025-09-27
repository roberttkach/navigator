"""Shared helpers for normalising instrumentation payloads."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence, Tuple, TypeVar

from navigator.app.service.navigator_runtime.api_contracts import (
    NavigatorRuntimeInstrument,
)

InstrumentT = TypeVar("InstrumentT", bound=NavigatorRuntimeInstrument)


def normalize_instrumentation(
    payload: Iterable[InstrumentT] | None,
) -> Tuple[InstrumentT, ...]:
    """Return a tuple-based representation of instrumentation payloads."""

    if payload is None:
        return ()
    if isinstance(payload, tuple):
        return payload
    return tuple(payload)


def as_sequence(
    payload: Iterable[InstrumentT] | None,
) -> Sequence[InstrumentT]:
    """Return a sequence compatible with runtime instrumentation hooks."""

    return normalize_instrumentation(payload)


__all__ = ["as_sequence", "normalize_instrumentation"]

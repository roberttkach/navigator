"""Inline payload validation helpers."""

from __future__ import annotations

from collections.abc import Iterable

from navigator.core.value.content import Payload

SHIELD_MESSAGE = "Inline message does not support media groups"
SHIELD_NODE_MESSAGE = "Inline message does not support multi-message nodes"


def _materialize(payloads: Payload | Iterable[Payload] | None) -> list[Payload]:
    if payloads is None:
        return []
    if isinstance(payloads, Payload):
        return [payloads]
    if isinstance(payloads, Iterable):
        return [item for item in payloads if item is not None]
    raise TypeError("payloads must be Payload or iterable of Payload")


def shield(
    scope,
    payloads: Payload | Iterable[Payload] | None,
    *,
    inline: bool | None = None,
) -> None:
    active = inline if inline is not None else bool(getattr(scope, "inline", None))
    if not active:
        return

    samples = _materialize(payloads)
    if len(samples) > 1:
        from navigator.core.error import InlineUnsupported

        raise InlineUnsupported(SHIELD_NODE_MESSAGE)

    for sample in samples:
        if getattr(sample, "group", None):
            from navigator.core.error import InlineUnsupported

            raise InlineUnsupported(SHIELD_MESSAGE)


__all__ = ["shield"]

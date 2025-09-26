"""Normalize payload bundles before rendering operations."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import List

from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


class RenderPreparer:
    """Normalize payload bundles before rendering operations."""

    def __init__(
        self,
        adapter: Callable[[Scope, Payload], Payload],
        shielder: Callable[[Scope, Sequence[Payload], bool], None] | None = None,
    ) -> None:
        self._adapt = adapter
        self._shield = shielder

    def prepare(
        self,
        scope: Scope,
        payloads: Sequence[Payload],
        *,
        inline: bool,
    ) -> List[Payload]:
        """Return payloads adapted to the current ``scope``."""

        bundle = [*payloads]
        if inline and self._shield is not None:
            self._shield(scope, bundle, inline=True)
        return [self._adapt(scope, payload) for payload in bundle]


__all__ = ["RenderPreparer"]


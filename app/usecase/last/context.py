"""Tail use-case data structures and decision helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ...internal.policy import PrimeEntryFactory, shield
from ....core.entity.history import Entry, Message
from ....core.service.rendering import decision
from ....core.service.rendering.config import RenderingConfig
from ....core.telemetry import LogCode, Telemetry, TelemetryChannel
from ....core.value.content import Payload, normalize
from ....core.value.message import Scope


@dataclass(slots=True)
class TailSnapshot:
    """Capture history snapshot relevant for tail operations."""

    marker: int | None
    history: list[Entry]
    index: Optional[int]

    @property
    def anchor(self) -> Entry | None:
        if self.index is None:
            return None
        if self.index < 0 or self.index >= len(self.history):
            return None
        return self.history[self.index]

    @property
    def head(self) -> Message | None:
        entry = self.anchor
        if entry and entry.messages:
            return entry.messages[0]
        return None

    @property
    def tail(self) -> Entry | None:
        if not self.history:
            return None
        return self.history[-1]

    def targets(self) -> list[int]:
        """Collect identifiers that should be deleted for resend scenarios."""

        head = self.head
        if head is None:
            return []
        bundle = [int(head.id)]
        bundle.extend(int(extra) for extra in (head.extras or []))
        return bundle

    def clone(self) -> list[Entry]:
        """Return a shallow copy of the underlying history list."""

        return list(self.history)

    @classmethod
    def build(cls, marker: int | None, history: list[Entry]) -> TailSnapshot:
        """Construct a snapshot by locating ``marker`` inside ``history``."""

        index: Optional[int] = None
        if marker is not None:
            for cursor in range(len(history) - 1, -1, -1):
                messages = history[cursor].messages
                if messages and int(messages[0].id) == int(marker):
                    index = cursor
                    break
        return cls(marker=marker, history=history, index=index)


@dataclass(slots=True)
class TailResolution:
    """Result of tail decision planning."""

    decision: decision.Decision
    payload: Payload
    base: Entry | None


class TailDecisionService:
    """Resolve reconciliation strategy for the tail flow."""

    def __init__(self, rendering: RenderingConfig, prime: PrimeEntryFactory) -> None:
        self._rendering = rendering
        self._prime = prime

    def resolve(
            self, scope: Scope, payload: Payload, snapshot: TailSnapshot
    ) -> TailResolution | None:
        """Return decision metadata for the given ``payload``."""

        normal = normalize(payload)
        shield(scope, [normal])

        anchor = snapshot.anchor
        head = snapshot.head
        if head is not None:
            choice = decision.decide(head, normal, self._rendering)
        else:
            if normal.media:
                choice = decision.Decision.EDIT_MEDIA
            elif normal.text is not None:
                choice = decision.Decision.EDIT_TEXT
            elif normal.reply is not None:
                choice = decision.Decision.EDIT_MARKUP
            else:
                return None

        if snapshot.marker is None:
            return None

        base = anchor if anchor is not None else self._prime.create(snapshot.marker, normal)
        return TailResolution(decision=choice, payload=normal, base=base)


class TailTelemetry:
    """Telemetry facade for tail operations."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def skip(self, *, op: str, note: str) -> None:
        """Emit a skip event with the provided ``note``."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op=op, note=note)


__all__ = [
    "TailDecisionService",
    "TailResolution",
    "TailSnapshot",
    "TailTelemetry",
]

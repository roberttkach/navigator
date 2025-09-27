"""Convert rendering outcomes into persisted history entries."""

from __future__ import annotations

from typing import List, Optional, Sequence

from ...core.entity.history import Entry, Message
from ...core.port.clock import Clock
from ...core.port.factory import ViewLedger
from ...core.util.entities import EntitySanitizer
from ...core.value.content import Payload
from .message_composer import MessageComposer
from .outcome import Outcome


def _view_if_known(ledger: ViewLedger, view: Optional[str]) -> Optional[str]:
    """Return ``view`` only when the ledger recognises the identifier."""

    if view and ledger.has(view):
        return view
    return None


class EntryMapper:
    """Translate rendering outcomes into persisted history entries."""

    def __init__(
            self,
            ledger: ViewLedger,
            clock: Clock,
            *,
            entities: EntitySanitizer,
    ) -> None:
        self._ledger = ledger
        self._clock = clock
        self._entities = entities

    def convert(
            self,
            outcome: "Outcome",
            payloads: List[Payload],
            state: Optional[str],
            view: Optional[str],
            root: bool,
            base: Optional[Entry] = None,
    ) -> Entry:
        """Build an entry from payloads and delivery outcome metadata."""

        messages = self._compose_messages(outcome, payloads, base)

        return Entry(
            state=state,
            view=_view_if_known(self._ledger, view),
            messages=messages,
            root=bool(root),
        )

    def _compose_messages(
            self,
            outcome: "Outcome",
            payloads: Sequence[Payload],
            base: Optional[Entry],
    ) -> List[Message]:
        timestamp = self._clock.now()
        composer = MessageComposer(
            outcome=outcome,
            base=base,
            timestamp=timestamp,
            entities=self._entities,
        )
        return [composer.build(index, payload) for index, payload in enumerate(payloads)]


__all__ = ["EntryMapper", "Outcome"]

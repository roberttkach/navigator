"""Timeline assembly helpers for the add use case."""

from __future__ import annotations

from typing import List, Optional

from navigator.app.map.entry import EntryMapper, Outcome
from navigator.core.entity.history import Entry
from navigator.core.value.content import Payload

from ..render_contract import RenderOutcome


class AppendEntryAssembler:
    """Build entries and timelines using render outcomes."""

    def __init__(self, mapper: EntryMapper) -> None:
        self._mapper = mapper

    def build_entry(
            self,
            adjusted: List[Payload],
            render: RenderOutcome,
            state: Optional[str],
            view: Optional[str],
            root: bool,
            *,
            base: Optional[Entry] = None,
    ) -> Entry:
        identifiers = list(render.ids)
        usable = adjusted[:len(identifiers)]
        outcome = Outcome(identifiers, list(render.extras), list(render.metas))
        return self._mapper.convert(
            outcome,
            usable,
            state,
            view,
            root,
            base=base,
        )

    @staticmethod
    def extend_timeline(records: List[Entry], entry: Entry, root: bool) -> List[Entry]:
        if root:
            return [entry]
        return [*records, entry]


__all__ = ["AppendEntryAssembler"]


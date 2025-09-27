"""Inline trimming workflows for tail history."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.value.message import Scope

from .journal import TailHistoryJournal
from .trimmer import TailInlineTrimmer


class TailInlineHistory:
    """Apply inline-specific trimming rules with telemetry reporting."""

    def __init__(
        self,
        trimmer: TailInlineTrimmer,
        *,
        journal: TailHistoryJournal,
    ) -> None:
        self._trimmer = trimmer
        self._journal = journal

    async def trim(
        self,
        history: Sequence[Entry],
        scope: Scope,
        *,
        op: str,
    ) -> list[Entry]:
        stored, marker = await self._trimmer.trim(history)
        self._journal.record_history_save(stored, op=op)
        self._journal.record_marker_mark(marker, op=op, scope=scope)
        return stored


__all__ = ["TailInlineHistory"]

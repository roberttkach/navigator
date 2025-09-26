"""Replace the latest history entry with freshly rendered payloads."""

from __future__ import annotations

from typing import List

from ...core.value.content import Payload
from ...core.value.message import Scope
from .replace_components import (
    ReplaceHistoryAccess,
    ReplaceHistoryWriter,
    ReplacePreparation,
)
from .replace_instrumentation import ReplaceInstrumentation


class Swapper:
    """Replace the trailing history entry with a newly mapped version."""

    def __init__(
            self,
            history: ReplaceHistoryAccess,
            preparation: ReplacePreparation,
            writer: ReplaceHistoryWriter,
            instrumentation: ReplaceInstrumentation,
    ):
        self._history = history
        self._prepare = preparation
        self._writer = writer
        self._instrumentation = instrumentation

    async def execute(self, scope: Scope, bundle: List[Payload]) -> None:
        """Replace history entry within ``scope`` using ``bundle`` payloads."""

        await self._instrumentation.traced(scope, bundle, self._perform)

    async def _perform(self, scope: Scope, bundle: List[Payload]) -> None:
        adjusted = self._prepare.normalize(scope, bundle)
        records = await self._history.snapshot()
        trail = records[-1] if records else None
        render = await self._prepare.plan(scope, adjusted, trail)

        if not render or not render.ids or not render.changed:
            self._instrumentation.render_skipped()
            return
        status = await self._history.status()

        entry = self._prepare.entry(trail, adjusted, render, status)
        timeline = self._prepare.timeline(records, entry)
        await self._writer.persist(timeline)

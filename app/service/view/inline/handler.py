"""Entry point for inline reconciliation handler."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from navigator.core.entity.history import Message
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .candidate import InlineCandidateBuilder
from .flows import InlineMediaFlow, InlineTextFlow
from .guard import InlineGuard
from .mediator import InlineEditMediator
from .remap import InlineRemapper
from .telemetry import InlineTelemetryAdapter
from .editor import InlineEditor, InlineOutcome
from ..executor import EditExecutor

if TYPE_CHECKING:
    from navigator.core.telemetry import Telemetry


@dataclass(slots=True)
class InlineHandler:
    """Mediate inline edits, remapping fallbacks when required."""

    guard: InlineGuard
    remapper: InlineRemapper
    editor: InlineEditor
    telemetry: Telemetry
    _candidate: InlineCandidateBuilder = field(init=False, repr=False)
    _media: InlineMediaFlow = field(init=False, repr=False)
    _text: InlineTextFlow = field(init=False, repr=False)

    def __post_init__(self) -> None:
        adapter = InlineTelemetryAdapter(self.telemetry)
        mediator = InlineEditMediator(self.editor)
        self._candidate = InlineCandidateBuilder()
        self._media = InlineMediaFlow(self.guard, self.remapper, mediator, adapter)
        self._text = InlineTextFlow(mediator, adapter)

    async def handle(
        self,
        *,
        scope: Scope,
        payload: Payload,
        tail: Message | None,
        executor: EditExecutor,
        config: RenderingConfig,
    ) -> InlineOutcome | None:
        """Plan inline reconciliation for the provided ``payload``."""

        entry = self._candidate.create(payload, tail)
        media = getattr(entry, "media", None)

        if media:
            return await self._media.handle(
                scope,
                entry,
                tail,
                executor,
                config,
            )

        return await self._text.handle(scope, entry, tail, executor)


__all__ = ["InlineHandler"]

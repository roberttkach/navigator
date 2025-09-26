"""Manual scenarios for tail manipulation workflows."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from navigator.app.service import (
    TailHistoryAccess,
    TailHistoryJournal,
    TailHistoryMutator,
    TailHistoryTracker,
)
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.last.context import TailDecisionService, TailTelemetry
from navigator.app.usecase.last.delete import TailDeleteWorkflow
from navigator.app.usecase.last.edit import TailEditWorkflow
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
from navigator.core.entity.media import MediaItem, MediaType
from navigator.core.error import InlineUnsupported
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.typing.result import TextMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .common import monitor


def decline() -> None:
    """Ensure inline edit workflow forbids media groups."""

    scope = Scope(chat=9, lang="en", inline="token")
    latest = SimpleNamespace(peek=AsyncMock(return_value=100), mark=AsyncMock())
    ledger = SimpleNamespace(recall=AsyncMock(), archive=AsyncMock())
    planner = SimpleNamespace(render=AsyncMock())
    executor = SimpleNamespace(
        delete=AsyncMock(),
        execute=AsyncMock(),
        refine=Mock(return_value=TextMeta(text="noop", inline=True)),
    )
    inline = SimpleNamespace(handle=AsyncMock())
    telemetry = monitor()
    journal = TailHistoryJournal.from_telemetry(telemetry)
    access = TailHistoryAccess(ledger=ledger, latest=latest)
    history = TailHistoryTracker(access=access, journal=journal)
    mutator = TailHistoryMutator()
    decision = TailDecisionService(rendering=RenderingConfig())
    inline_coord = InlineEditCoordinator(
        handler=inline,
        executor=executor,
        rendering=RenderingConfig(),
    )
    mutation = MessageEditCoordinator(
        executor=executor,
        history=history,
        mutator=mutator,
    )
    telemetry_service = TailTelemetry(telemetry)
    tail_delete = TailDeleteWorkflow(
        history=history,
        mutation=mutation,
        telemetry=telemetry_service,
    )
    tail_edit = TailEditWorkflow(
        history=history,
        decision=decision,
        inline=inline_coord,
        mutation=mutation,
        telemetry=telemetry_service,
    )
    tailer = Tailer(history=history, delete=tail_delete, edit=tail_edit)
    payload = Payload(
        group=[
            MediaItem(type=MediaType.PHOTO, path="file-x"),
            MediaItem(type=MediaType.PHOTO, path="file-y"),
        ]
    )

    try:
        asyncio.run(tailer.edit(scope, payload))
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support media groups"
    else:
        raise AssertionError("InlineUnsupported was not raised")

    ledger.recall.assert_not_awaited()


__all__ = ["decline"]

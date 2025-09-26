"""Manual scenarios around history restoration."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from navigator.app.usecase.set import Setter
from navigator.app.usecase.set_components import (
    HistoryReconciler,
    HistoryRestorationPlanner,
    PayloadReviver,
    StateSynchronizer,
)
from navigator.core.entity.history import Entry
from navigator.core.error import InlineUnsupported, StateNotFound
from navigator.core.value.message import Scope

from .common import monitor


def absence() -> None:
    """Exercise setter failure when state is missing."""

    scope = Scope(chat=5, lang="ru")
    ledger = SimpleNamespace(recall=AsyncMock(return_value=[]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock())
    restorer = SimpleNamespace(revive=AsyncMock())
    planner = SimpleNamespace(render=AsyncMock())
    latest = SimpleNamespace(mark=AsyncMock())
    telemetry = monitor()
    state = StateSynchronizer(state=status, telemetry=telemetry)
    reviver = PayloadReviver(state, restorer)
    reconciliation = HistoryReconciler.from_components(
        ledger=ledger,
        latest=latest,
        telemetry=telemetry,
    )
    plan_builder = HistoryRestorationPlanner(ledger=ledger, telemetry=telemetry)
    setter = Setter(
        planner=plan_builder,
        state=state,
        reviver=reviver,
        renderer=planner,
        reconciler=reconciliation,
        telemetry=telemetry,
    )

    try:
        asyncio.run(setter.execute(scope, goal="target", context={}))
    except StateNotFound:
        pass
    else:
        raise AssertionError("StateNotFound was not raised")

    ledger.archive.assert_not_awaited()
    planner.render.assert_not_awaited()


def surface() -> None:
    """Validate inline failure propagates to history reconstruction."""

    scope = Scope(chat=5, lang="ru", inline="token")
    target = Entry(state="target", view="dynamic", messages=[])
    tail = Entry(state="tail", view=None, messages=[])
    ledger = SimpleNamespace(recall=AsyncMock(return_value=[target, tail]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock(return_value={}))
    restorer = SimpleNamespace(
        revive=AsyncMock(side_effect=InlineUnsupported("inline_dynamic_multi_payload"))
    )
    planner = SimpleNamespace(render=AsyncMock())
    latest = SimpleNamespace(mark=AsyncMock())
    telemetry = monitor()
    state = StateSynchronizer(state=status, telemetry=telemetry)
    reviver = PayloadReviver(state, restorer)
    reconciliation = HistoryReconciler.from_components(
        ledger=ledger,
        latest=latest,
        telemetry=telemetry,
    )
    plan_builder = HistoryRestorationPlanner(ledger=ledger, telemetry=telemetry)
    setter = Setter(
        planner=plan_builder,
        state=state,
        reviver=reviver,
        renderer=planner,
        reconciler=reconciliation,
        telemetry=telemetry,
    )

    try:
        asyncio.run(setter.execute(scope, goal="target", context={}))
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")

    planner.render.assert_not_awaited()
    latest.mark.assert_not_awaited()


__all__ = ["absence", "surface"]

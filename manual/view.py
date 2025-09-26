"""Manual scenarios targeting view planning and restoration."""
from __future__ import annotations

import asyncio
from navigator.app.service.view.planner import RenderPreparer, ViewPlanner
from navigator.app.service.view.policy import adapt
from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.internal.policy import shield
from navigator.core.entity.history import Entry
from navigator.core.entity.media import MediaItem, MediaType
from navigator.core.error import InlineUnsupported
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .common import monitor


class _InlineStub:
    async def plan(self, scope, fresh, ledger, state):
        return False


class _RegularStub:
    async def plan(self, scope, fresh, ledger, state):
        return False


def veto() -> None:
    """Ensure inline restoration forbids multi-message payloads."""

    async def forge():
        return [Payload(text="one"), Payload(text="two")]

    class Ledger:
        def __init__(self) -> None:
            self._mapping = {"dynamic": forge}

        def get(self, key: str):
            if key not in self._mapping:
                raise KeyError(key)
            return self._mapping[key]

    entry = Entry(state="alpha", view="dynamic", messages=[])
    restorer = ViewRestorer(ledger=Ledger(), telemetry=monitor())

    try:
        asyncio.run(restorer.revive(entry, {}, inline=True))
    except InlineUnsupported as error:
        assert str(error) == "inline_dynamic_multi_payload"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def assent() -> None:
    """Verify regular restoration succeeds for multi-message payloads."""

    async def forge():
        return [Payload(text="one"), Payload(text="two")]

    class Ledger:
        def __init__(self) -> None:
            self._mapping = {"dynamic": forge}

        def get(self, key: str):
            if key not in self._mapping:
                raise KeyError(key)
            return self._mapping[key]

    entry = Entry(state="alpha", view="dynamic", messages=[])
    restorer = ViewRestorer(ledger=Ledger(), telemetry=monitor())

    restored = asyncio.run(restorer.revive(entry, {}, inline=False))

    assert [payload.text for payload in restored] == ["one", "two"]


def rebuff() -> None:
    """Confirm inline planner rejects multi-message nodes."""

    scope = Scope(chat=7, lang="en", inline="token")
    preparer = RenderPreparer(adapter=adapt, shielder=shield)
    planner = ViewPlanner(inline=_InlineStub(), regular=_RegularStub(), preparer=preparer)

    try:
        asyncio.run(
            planner.render(
                scope,
                [Payload(text="one"), Payload(text="two")],
                trail=None,
                inline=True,
            )
        )
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support multi-message nodes"
    else:
        raise AssertionError("InlineUnsupported was not raised")


def refuse() -> None:
    """Confirm inline planner rejects media groups."""

    scope = Scope(chat=8, lang="en", inline="token")
    preparer = RenderPreparer(adapter=adapt, shielder=shield)
    planner = ViewPlanner(inline=_InlineStub(), regular=_RegularStub(), preparer=preparer)
    album = [
        MediaItem(type=MediaType.PHOTO, path="file-a", caption="a"),
        MediaItem(type=MediaType.PHOTO, path="file-b", caption="b"),
    ]

    try:
        asyncio.run(
            planner.render(
                scope,
                [Payload(group=album)],
                trail=None,
                inline=True,
            )
        )
    except InlineUnsupported as error:
        assert str(error) == "Inline message does not support media groups"
    else:
        raise AssertionError("InlineUnsupported was not raised")


__all__ = ["assent", "rebuff", "refuse", "veto"]

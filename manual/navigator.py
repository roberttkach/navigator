"""Manual scenarios operating on the navigator facade."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
from navigator.core.error import StateNotFound
from navigator.core.value.message import Scope
from navigator.presentation.alerts import missing
from navigator.presentation.navigator import Navigator



class _StateStub:
    def __init__(self, scope: Scope) -> None:
        self._scope = scope
        self._setter = AsyncMock(side_effect=StateNotFound("missing"))
        self._alarm = SimpleNamespace(execute=AsyncMock())

    async def set(self, state: str, context: dict[str, object] | None = None) -> None:
        try:
            await self._setter(self._scope, state, context or {})
        except StateNotFound:
            await self._alarm.execute(self._scope, text=missing(self._scope))

    async def alert(self) -> None:
        await self._alarm.execute(self._scope)

    # Testing helpers -------------------------------------------------
    @property
    def setter(self) -> AsyncMock:
        return self._setter

    @property
    def alarm(self) -> AsyncMock:
        return self._alarm.execute


def siren() -> None:
    """Ensure missing states trigger an alarm."""

    scope = Scope(chat=10, lang="ru")
    state = _StateStub(scope)
    history = SimpleNamespace(
        add=AsyncMock(),
        replace=AsyncMock(),
        rebase=AsyncMock(),
        back=AsyncMock(),
        pop=AsyncMock(),
    )
    tail = SimpleNamespace(edit=AsyncMock())
    runtime = NavigatorRuntime(history=history, state=state, tail=tail)
    navigator = Navigator(runtime)

    asyncio.run(navigator.set("missing"))

    state.setter.assert_awaited_once_with(scope, "missing", {})
    state.alarm.assert_awaited_once()
    call = state.alarm.await_args
    assert call.args == (scope,)
    assert call.kwargs == {"text": missing(scope)}


__all__ = ["siren"]

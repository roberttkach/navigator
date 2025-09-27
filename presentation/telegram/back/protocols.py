"""Protocols shared across telegram retreat components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from navigator.app.service.navigator_runtime.back_context import NavigatorBackContext


class RetreatHistory(Protocol):
    async def back(self, context: NavigatorBackContext) -> None: ...


class NavigatorBack(Protocol):
    history: RetreatHistory


Translator = Callable[[str, str], str]


__all__ = ["NavigatorBack", "RetreatHistory", "Translator"]

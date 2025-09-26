"""Protocols shared across telegram retreat components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class NavigatorBack(Protocol):
    async def back(self, context: dict[str, Any]) -> None: ...


Translator = Callable[[str, str], str]


__all__ = ["NavigatorBack", "Translator"]

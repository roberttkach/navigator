from __future__ import annotations

import typing
from datetime import datetime
from typing import Protocol


@typing.runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime:
        ...


__all__ = ["Clock"]

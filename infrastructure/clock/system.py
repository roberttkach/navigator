from __future__ import annotations

from datetime import datetime, timezone

from domain.port.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


__all__ = ["SystemClock"]

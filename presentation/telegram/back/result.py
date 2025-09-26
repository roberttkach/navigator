"""Value objects representing retreat workflow results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetreatResult:
    """Represents the outcome of a retreat workflow execution."""

    note: str | None = None

    @property
    def success(self) -> bool:
        return self.note is None

    @classmethod
    def ok(cls) -> "RetreatResult":
        return cls()

    @classmethod
    def failed(cls, note: str) -> "RetreatResult":
        return cls(note=note)


__all__ = ["RetreatResult"]

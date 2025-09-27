"""Abstractions exposing runtime redaction settings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeRedactionConfig:
    """Structured representation of redaction options."""

    value: str = ""

    @classmethod
    def from_settings(cls, settings: object) -> "RuntimeRedactionConfig":
        """Build configuration from infrastructure settings."""

        value = getattr(settings, "redaction", "")
        return cls(value=value)


__all__ = ["RuntimeRedactionConfig"]

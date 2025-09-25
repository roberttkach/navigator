from __future__ import annotations

"""Provide immutable messaging scope descriptors."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scope:
    """Describe the addressing context for an outgoing message."""

    chat: int | None
    lang: str | None = None
    inline: str | None = None
    business: str | None = None
    category: str | None = None
    topic: int | None = None
    direct: bool = False

    @property
    def uses_inline_mode(self) -> bool:
        """Report whether the scope expects inline message handling."""

        return bool(self.inline)

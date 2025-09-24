from __future__ import annotations

from html import escape
from typing import Optional


def purify(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return escape(text)


__all__ = ["purify"]

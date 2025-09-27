"""Helpers for translating public scope DTOs into domain objects."""
from __future__ import annotations

from .contracts import ScopeDTO
from ..core.value.message import Scope


def scope_from_dto(dto: ScopeDTO) -> Scope:
    """Translate external ``ScopeDTO`` structures into domain scopes."""

    return Scope(
        chat=getattr(dto, "chat", None),
        lang=getattr(dto, "lang", None),
        inline=getattr(dto, "inline", None),
        business=getattr(dto, "business", None),
        category=getattr(dto, "category", None),
        topic=getattr(dto, "topic", None),
        direct=bool(getattr(dto, "direct", False)),
    )


__all__ = ["scope_from_dto"]

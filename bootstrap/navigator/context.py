"""Bootstrap context and DTO translation helpers."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.api.contracts import ScopeDTO, ViewLedgerDTO
from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.value.message import Scope

from .container_types import ViewContainerFactory


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


@dataclass(frozen=True)
class BootstrapContext:
    """Collect payloads required to assemble the navigator runtime."""

    event: object
    state: object
    ledger: ViewLedgerDTO
    scope: ScopeDTO
    missing_alert: MissingAlert | None = None
    view_container: ViewContainerFactory | None = None


__all__ = ["BootstrapContext", "scope_from_dto", "ViewContainerFactory"]

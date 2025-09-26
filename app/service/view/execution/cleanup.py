"""Deletion routines executed after edit operations."""

from __future__ import annotations

from navigator.core.port.message import MessageGateway
from navigator.core.value.message import Scope


class EditCleanup:
    """Encapsulate deletion routines executed after edit operations."""

    def __init__(self, gateway: MessageGateway) -> None:
        self._gateway = gateway

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        if identifiers:
            await self._gateway.delete(scope, identifiers)


__all__ = ["EditCleanup"]


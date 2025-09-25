"""Adapters bridging DTO infrastructure with the domain layer."""
from __future__ import annotations

from navigator.api.contracts import ViewLedgerDTO
from navigator.core.port.factory import ViewForge, ViewLedger


class LedgerAdapter(ViewLedger):
    """Expose a DTO-backed ledger through the domain ``ViewLedger``."""

    def __init__(self, ledger: ViewLedgerDTO) -> None:
        self._ledger = ledger

    def get(self, key: str) -> ViewForge:
        """Return a forge callable for ``key`` ensuring callability."""

        forge = self._ledger.get(key)
        if not callable(forge):
            raise TypeError(f"Ledger forge for '{key}' is not callable")
        return forge

    def has(self, key: str) -> bool:
        """Return ``True`` when the underlying ledger exposes ``key``."""

        return bool(self._ledger.has(key))


__all__ = ["LedgerAdapter"]

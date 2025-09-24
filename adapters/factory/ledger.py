from __future__ import annotations

import logging
from typing import Dict

from navigator.domain.port.factory import ViewForge, ViewLedger as ViewLedgerProtocol
from navigator.log import LogCode, jlog

logger = logging.getLogger(__name__)


def _stamp(forger: ViewForge) -> str:
    module = getattr(forger, "__module__", "")
    qualname = getattr(forger, "__qualname__", getattr(forger, "__name__", ""))
    return f"{module}:{qualname}"


def key(forger: ViewForge) -> str:
    return _stamp(forger)


class ViewLedger(ViewLedgerProtocol):
    def __init__(self) -> None:
        self._ledger: Dict[str, ViewForge] = {}

    def register(self, name: str, forge: ViewForge) -> None:
        if name in self._ledger:
            jlog(logger, logging.WARNING, LogCode.REGISTRY_REGISTER, key=name, note="duplicate")
            raise KeyError(f"Factory already registered for key: {name}")
        self._ledger[name] = forge
        jlog(logger, logging.INFO, LogCode.REGISTRY_REGISTER, key=name, note="ok")

    def enlist(self, forge: ViewForge) -> str:
        signature = _stamp(forge)
        self.register(signature, forge)
        return signature

    def get(self, key: str) -> ViewForge:
        try:
            found = self._ledger[key]
            jlog(logger, logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=True)
            return found
        except KeyError as e:
            jlog(logger, logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=False)
            raise KeyError(f"Factory not found for key: {key}") from e

    def has(self, key: str) -> bool:
        exists = key in self._ledger
        jlog(logger, logging.DEBUG, LogCode.REGISTRY_HAS, key=key, found=exists)
        return exists


__all__ = ["ViewLedger", "key"]


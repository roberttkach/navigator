from __future__ import annotations

import logging
from typing import Dict

from navigator.core.port.factory import ViewForge, ViewLedger as ViewLedgerProtocol
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


def _stamp(forger: ViewForge) -> str:
    module = getattr(forger, "__module__", "")
    qualname = getattr(forger, "__qualname__", getattr(forger, "__name__", ""))
    return f"{module}:{qualname}"


def key(forger: ViewForge) -> str:
    return _stamp(forger)


class ViewLedger(ViewLedgerProtocol):
    def __init__(self, telemetry: Telemetry | None = None) -> None:
        self._ledger: Dict[str, ViewForge] = {}
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def _emit(self, level: int, code: LogCode, /, **fields: object) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    def register(self, name: str, forge: ViewForge) -> None:
        if name in self._ledger:
            self._emit(logging.WARNING, LogCode.REGISTRY_REGISTER, key=name, note="duplicate")
            raise KeyError(f"Factory already registered for key: {name}")
        self._ledger[name] = forge
        self._emit(logging.INFO, LogCode.REGISTRY_REGISTER, key=name, note="ok")

    def enlist(self, forge: ViewForge) -> str:
        signature = _stamp(forge)
        self.register(signature, forge)
        return signature

    def get(self, key: str) -> ViewForge:
        try:
            found = self._ledger[key]
            self._emit(logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=True)
            return found
        except KeyError as e:
            self._emit(logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=False)
            raise KeyError(f"Factory not found for key: {key}") from e

    def has(self, key: str) -> bool:
        exists = key in self._ledger
        self._emit(logging.DEBUG, LogCode.REGISTRY_HAS, key=key, found=exists)
        return exists


__all__ = ["ViewLedger", "key"]


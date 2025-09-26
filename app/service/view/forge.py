"""Utilities for resolving and invoking view forges."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping
from typing import Any, Dict, List, Optional, Tuple

from ....core.port.factory import ViewLedger
from ....core.telemetry import LogCode, TelemetryChannel
from ....core.value.content import Payload

_Forge = Callable[..., Awaitable[Optional[Payload | List[Payload]]]]
_SUPPLIES_ATTR = "__navigator_supplies__"


def forge_supplies(*names: str) -> Callable[[_Forge], _Forge]:
    """Annotate ``forge`` with the context keys it expects."""

    required = _normalize_supplies(names)

    def decorator(forge: _Forge) -> _Forge:
        setattr(forge, _SUPPLIES_ATTR, required)
        return forge

    return decorator


def _normalize_supplies(names: Iterable[str]) -> Tuple[str, ...]:
    """Return stable, de-duplicated supply names."""

    unique: Dict[str, None] = {}
    for name in names:
        unique[str(name)] = None
    return tuple(unique.keys())


def _declared_supplies(forge: _Forge) -> Tuple[str, ...]:
    """Fetch the supply declaration attached to ``forge`` if present."""

    declared = getattr(forge, _SUPPLIES_ATTR, ())
    if isinstance(declared, str):
        return (declared,)
    if isinstance(declared, Iterable):
        return _normalize_supplies(declared)
    return ()


class ForgeResolver:
    """Resolve view forges from the configured ledger."""

    def __init__(self, ledger: ViewLedger, channel: TelemetryChannel) -> None:
        self._ledger = ledger
        self._channel = channel

    def resolve(self, key: str) -> Optional[_Forge]:
        try:
            return self._ledger.get(key)
        except KeyError:
            self._channel.emit(
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note="factory_not_found",
            )
            return None


class ForgeSuppliesExtractor:
    """Derive forge arguments from the provided context mapping."""

    def extract(self, forge: _Forge, context: Mapping[str, Any]) -> Dict[str, Any]:
        required = _declared_supplies(forge)
        if not required:
            return {}
        supplies: Dict[str, Any] = {}
        missing: list[str] = []
        for name in required:
            if name in context:
                supplies[name] = context[name]
            else:
                missing.append(name)
        if missing:
            raise KeyError(f"missing_supplies:{','.join(sorted(missing))}")
        return supplies


class ForgeInvoker:
    """Invoke dynamic forges while reporting telemetry on failures."""

    def __init__(
        self,
        channel: TelemetryChannel,
        extractor: ForgeSuppliesExtractor | None = None,
    ) -> None:
        self._channel = channel
        self._extractor = extractor or ForgeSuppliesExtractor()

    async def invoke(
        self,
        key: str,
        forge: _Forge,
        context: Mapping[str, Any],
    ) -> Optional[Payload | List[Payload]]:
        try:
            supplies = self._extractor.extract(forge, context)
            return await forge(**supplies)
        except Exception as exc:  # pragma: no cover - defensive
            self._channel.emit(
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note=type(exc).__name__,
                exc_info=True,
                error={"type": type(exc).__name__},
            )
            return None


__all__ = [
    "ForgeInvoker",
    "ForgeResolver",
    "ForgeSuppliesExtractor",
    "_Forge",
    "forge_supplies",
]

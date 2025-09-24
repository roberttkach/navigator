from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, FrozenSet

from domain.log.code import LogCode
from domain.log.emit import jlog


class SignatureScreen:
    def __init__(self) -> None:
        self._seen: set[tuple[str, FrozenSet[str]]] = set()
        self._logger = logging.getLogger(__name__)

    def _signature(self, target: Any) -> set[str] | None:
        obj = target.__init__ if inspect.isclass(target) else target
        try:
            sig = inspect.signature(obj)
        except Exception:  # pragma: no cover - defensive
            return None
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return None
        return set(sig.parameters.keys())

    def filter(self, target: Any, extra: Dict[str, Any] | None) -> Dict[str, Any]:
        if not extra:
            return {}
        allowed = self._signature(target)
        if allowed is None:
            mark = (getattr(target, "__name__", str(target)), frozenset(extra.keys()))
            if mark not in self._seen:
                self._seen.add(mark)
                jlog(
                    self._logger,
                    logging.DEBUG,
                    LogCode.EXTRA_FILTERED_OUT,
                    stage="any.warn",
                    target=mark[0],
                    keys=sorted(mark[1]),
                )
            return dict(extra)
        filtered = {k: v for k, v in extra.items() if k in allowed}
        if set(filtered.keys()) != set(extra.keys()):
            jlog(
                self._logger,
                logging.DEBUG,
                LogCode.EXTRA_FILTERED_OUT,
                stage="signature", target=getattr(target, "__name__", str(target)),
                before=sorted(extra.keys()),
                after=sorted(filtered.keys()),
                filtered_keys=sorted(set(extra) - set(filtered)),
            )
        return filtered


__all__ = ["SignatureScreen"]

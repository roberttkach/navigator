import inspect
import logging
from typing import Any, Dict, FrozenSet

from ...domain.log.emit import jlog
from ...logging.code import LogCode

_seen: set[tuple[str, FrozenSet[str]]] = set()
_logger = logging.getLogger(__name__)


def _sig_params(target: Any) -> set:
    obj = target.__init__ if inspect.isclass(target) else target
    try:
        sig = inspect.signature(obj)
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return {"__ANY__"}
        return set(sig.parameters.keys())
    except Exception:
        return {"__ANY__"}


def accept_for(target: Any, extra: Dict[str, Any] | None) -> Dict[str, Any]:
    if not extra:
        return {}
    allowed = _sig_params(target)
    if "__ANY__" in allowed:
        tgt = getattr(target, "__name__", str(target))
        keys = frozenset(extra.keys())
        mark = (tgt, keys)
        if mark not in _seen:
            _seen.add(mark)
            jlog(_logger, logging.DEBUG, LogCode.EXTRA_FILTERED_OUT, stage="any.warn", target=tgt, keys=sorted(keys))
        return dict(extra)
    return {k: v for k, v in extra.items() if k in allowed}

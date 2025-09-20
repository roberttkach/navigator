from __future__ import annotations

import logging
import warnings
from typing import Any

from ..adapters.factory.registry import default as _default_registry
from ..adapters.storage.keys import FSM_HISTORY_KEY
from ..domain.log.code import LogCode
from ..domain.log.emit import jlog

logger = logging.getLogger(__name__)


async def cleanse(state: Any, registry=_default_registry) -> None:
    """Clear history entries that point to unregistered views."""

    registry_to_use = registry if registry is not None else _default_registry

    data = await state.get_data()
    items = data.get(FSM_HISTORY_KEY, [])
    if not isinstance(items, list):
        return

    cleared: list[str] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        view_key = entry.get("view")
        if isinstance(view_key, str) and not registry_to_use.has(view_key):
            cleared.append(view_key)
            entry["view"] = None

    if not cleared:
        return

    await state.update_data({FSM_HISTORY_KEY: items})
    jlog(
        logger,
        logging.INFO,
        LogCode.HISTORY_TRIM,
        count=len(cleared),
        keys=cleared,
        note="views_purged",
    )


async def purge_invalid_views(state: Any, registry=_default_registry) -> None:
    warnings.warn("purge_invalid_views is deprecated; use cleanse", DeprecationWarning, stacklevel=2)
    await cleanse(state, registry)

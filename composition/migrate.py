from __future__ import annotations

import logging
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
    changed = False
    for entry in items:
        if not isinstance(entry, dict):
            continue
        view_key = entry.get("view")
        if isinstance(view_key, str) and not registry_to_use.has(view_key):
            cleared.append(view_key)
            entry["view"] = None
            changed = True

        messages = entry.get("messages")
        if not isinstance(messages, list):
            continue
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            if "aux_ids" in msg:
                aux = msg.pop("aux_ids")
                if "extras" not in msg and aux is not None:
                    msg["extras"] = aux
                changed = True

            if "inline_id" in msg:
                inline_value = msg.pop("inline_id")
                if msg.get("inline") is None and inline_value is not None:
                    msg["inline"] = inline_value
                changed = True

            if "by_bot" in msg:
                by_bot = msg.pop("by_bot")
                if "automated" not in msg:
                    msg["automated"] = bool(by_bot)
                changed = True

    if not (cleared or changed):
        return

    await state.update_data({FSM_HISTORY_KEY: items})
    if cleared:
        jlog(
            logger,
            logging.INFO,
            LogCode.HISTORY_TRIM,
            count=len(cleared),
            keys=cleared,
            note="views_purged",
        )



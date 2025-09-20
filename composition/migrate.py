from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..adapters.factory.registry import default as _default_registry
from ..adapters.storage.keys import FSM_HISTORY_KEY, FSM_LAST_ID_KEY, FSM_GRAPH_NODES_KEY, FSM_GRAPH_EDGES_KEY, \
    FSM_TEMP_KEY
from ..domain.log.emit import jlog
from ..domain.log.code import LogCode

logger = logging.getLogger(__name__)

_FWD_MAP: Dict[str, str] = {
    "navigator_history": FSM_HISTORY_KEY,
    "navigator_last_id": FSM_LAST_ID_KEY,
    "navigator_graph_nodes": FSM_GRAPH_NODES_KEY,
    "navigator_graph_edges": FSM_GRAPH_EDGES_KEY,
    "navigator_temporary": FSM_TEMP_KEY,
}
_BWD_MAP: Dict[str, str] = {v: k for k, v in _FWD_MAP.items()}


async def _rename_keys(state: Any, mapping: Dict[str, str]) -> None:
    data = await state.get_data()
    updates: Dict[str, Any] = {}
    clears: Dict[str, Any] = {}
    for src, dst in mapping.items():
        if src in data:
            updates[dst] = data.get(src)
            clears[src] = None
    if updates:
        await state.update_data(updates)
    if clears:
        await state.update_data(clears)


async def rename_keys_forward(state: Any) -> None:
    await _rename_keys(state, _FWD_MAP)


async def rename_keys_backward(state: Any) -> None:
    await _rename_keys(state, _BWD_MAP)


async def purge_invalid_views(state: Any, registry) -> None:
    data = await state.get_data()
    items = data.get(FSM_HISTORY_KEY, [])
    if not isinstance(items, list):
        return
    changed = False
    cleared: List[str] = []
    for d in items:
        if isinstance(d, Dict):
            vk = d.get("view")
            if isinstance(vk, str) and not registry.has(vk):
                cleared.append(vk)
                d["view"] = None
                changed = True
    if changed:
        await state.update_data({FSM_HISTORY_KEY: items})
        jlog(logger, logging.INFO, LogCode.MIG_VIEW_CLEARED, count=len(cleared), keys=cleared)


def _has_legacy_paths(entry_dict: Dict[str, Any]) -> bool:
    msgs = entry_dict.get("messages") or []
    for m in msgs:
        md = (m or {}).get("media")
        if isinstance(md, dict) and "path" in md:
            return True
        gr = (m or {}).get("group") or []
        for it in gr:
            if isinstance(it, dict) and "path" in it:
                return True
    return False


async def run(state: Any, registry=_default_registry) -> None:
    await rename_keys_forward(state)
    data = await state.get_data()
    items = data.get(FSM_HISTORY_KEY, [])
    if not isinstance(items, list):
        return

    # Одноразовая очистка истории при старой схеме хранения path в media/group
    legacy = any(isinstance(d, Dict) and _has_legacy_paths(d) for d in items)
    if legacy:
        await state.update_data({FSM_HISTORY_KEY: []})
        jlog(logger, logging.INFO, LogCode.MIG_VIEW_CLEARED, count=0, keys=[], note="schema_reset")
        return

    # Приведение плоских записей к messages[...], фиксация ts
    changed = False
    now_iso = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for d in items:
        if not isinstance(d, Dict):
            continue
        if "messages" not in d:
            ca = d.get("ts")
            ts = now_iso if not isinstance(ca, str) else ca
            msg = {
                "id": d.get("id", 0),
                "text": d.get("text"),
                "media": d.get("media"),
                "group": d.get("group"),
                "markup": d.get("markup"),
                "preview": d.get("preview"),
                "extra": d.get("extra"),
                "by_bot": d.get("by_bot", True),
                "ts": ts,
            }
            d["messages"] = [msg]
            d["root"] = bool(d.get("root", False) or d.get("is_main", False))
            for k in ("id", "text", "media", "group", "markup", "preview", "extra", "by_bot", "ts", "is_main"):
                if k in d:
                    d.pop(k, None)
            changed = True

    if changed:
        await state.update_data({FSM_HISTORY_KEY: items})

    await purge_invalid_views(state, registry)

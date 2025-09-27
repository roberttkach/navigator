"""Chronicle storage helpers for FSM namespaces."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

from .context import StateContext
from .keys import FSM_HISTORY_FIELD, FSM_NAMESPACE_KEY


class ChronicleStorage:
    """Persist FSM chronicle namespaces in the underlying state context."""

    def __init__(self, state: StateContext) -> None:
        self._state = state

    async def read(self) -> "ChronicleNamespace":
        data = await self._state.get_data()
        namespace = data.get(FSM_NAMESPACE_KEY)
        payload = namespace if isinstance(namespace, dict) else {}
        return ChronicleNamespace(payload)

    async def write(self, namespace: "ChronicleNamespace") -> None:
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace.dump()})


class ChronicleNamespace:
    """Access helpers around FSM namespace payloads."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload: MutableMapping[str, Any] = dict(payload)

    def history(self) -> List[Mapping[str, Any]]:
        raw = self._payload.get(FSM_HISTORY_FIELD, [])
        return raw if isinstance(raw, list) else []

    def update_history(self, history: Iterable[Mapping[str, Any]]) -> None:
        self._payload[FSM_HISTORY_FIELD] = list(history)

    def dump(self) -> Dict[str, Any]:
        return dict(self._payload)


__all__ = ["ChronicleNamespace", "ChronicleStorage"]

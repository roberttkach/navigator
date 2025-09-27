"""Shared rewind context contracts decoupled from service details."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, MutableMapping


@dataclass(frozen=True, slots=True)
class NavigatorBackEvent:
    """Structured representation of UI callback data relevant for rewind."""

    id: str
    data: str | None
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze ``metadata`` to avoid accidental mutation leaks."""

        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata))
        )

    def as_mapping(self) -> dict[str, Any]:
        """Return the event fields as a plain mapping."""

        data: MutableMapping[str, Any] = {
            "id": self.id,
            "data": self.data,
        }
        if self.source is not None:
            data["source"] = self.source
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return dict(data)


@dataclass(frozen=True, slots=True)
class NavigatorBackContext:
    """Stable contract passed from presentation into rewind use cases."""

    payload: Mapping[str, Any]
    event: NavigatorBackEvent | None = None

    def as_mapping(self) -> dict[str, Any]:
        """Return a mutable mapping merging payload and structured event."""

        data = dict(self.payload)
        if self.event is not None:
            data.setdefault("event", self.event.as_mapping())
        return data

    def handler_names(self) -> Iterable[str]:
        """Return the logical handler keys present inside the context."""

        handlers = set(self.payload.keys())
        if self.event is not None:
            handlers.add("event")
        return sorted(handlers)


__all__ = ["NavigatorBackContext", "NavigatorBackEvent"]


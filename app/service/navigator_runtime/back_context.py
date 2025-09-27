"""Domain oriented context objects for navigator back operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class NavigatorBackEvent:
    """Structured representation of UI callback data relevant for rewind."""

    id: str
    data: str | None
    inline_message_id: str | None
    chat_instance: str | None
    message_id: int | None
    message_chat_id: int | None
    message_thread_id: int | None
    message_chat_type: str | None
    user_id: int | None
    user_language: str | None
    user_username: str | None
    user_first_name: str | None
    user_last_name: str | None

    def as_mapping(self) -> dict[str, Any]:
        """Return the event fields as a plain mapping."""

        return {
            "id": self.id,
            "data": self.data,
            "inline_message_id": self.inline_message_id,
            "chat_instance": self.chat_instance,
            "message_id": self.message_id,
            "message_chat_id": self.message_chat_id,
            "message_thread_id": self.message_thread_id,
            "message_chat_type": self.message_chat_type,
            "user_id": self.user_id,
            "user_language": self.user_language,
            "user_username": self.user_username,
            "user_first_name": self.user_first_name,
            "user_last_name": self.user_last_name,
        }


@dataclass(frozen=True, slots=True)
class NavigatorBackContext:
    """Stable contract passed from the presentation layer into rewind use cases."""

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

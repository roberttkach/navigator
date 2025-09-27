"""Context helpers for telegram retreat workflows."""

from __future__ import annotations

from typing import Mapping, MutableMapping

from aiogram.types import CallbackQuery, Message, User

from navigator.core.contracts.back import NavigatorBackContext, NavigatorBackEvent


class MessageMetadataExtractor:
    """Retrieve message-related attributes from callback payloads."""

    def chat_id(self, message: Message | None) -> int | None:
        chat = getattr(message, "chat", None)
        return getattr(chat, "id", None)

    def chat_type(self, message: Message | None) -> str | None:
        chat = getattr(message, "chat", None)
        return getattr(chat, "type", None)

    def identifier(self, message: Message | None) -> int | None:
        return getattr(message, "message_id", None)

    def thread(self, message: Message | None) -> int | None:
        return getattr(message, "message_thread_id", None)


class UserMetadataExtractor:
    """Retrieve user-related attributes from callback payloads."""

    def identifier(self, user: User | None) -> int | None:
        return getattr(user, "id", None)

    def language(self, user: User | None) -> str | None:
        code = getattr(user, "language_code", None)
        return str(code) if code is not None else None

    def username(self, user: User | None) -> str | None:
        return getattr(user, "username", None)

    def first_name(self, user: User | None) -> str | None:
        return getattr(user, "first_name", None)

    def last_name(self, user: User | None) -> str | None:
        return getattr(user, "last_name", None)


class CallbackMetadataSanitizer:
    """Collect and clean callback metadata for navigator events."""

    def __init__(
        self,
        message: MessageMetadataExtractor | None = None,
        user: UserMetadataExtractor | None = None,
    ) -> None:
        self._message = message or MessageMetadataExtractor()
        self._user = user or UserMetadataExtractor()

    def sanitize(self, cb: CallbackQuery) -> Mapping[str, object]:
        metadata: MutableMapping[str, object | None] = {
            "inline_message_id": cb.inline_message_id,
            "chat_instance": cb.chat_instance,
            "message_id": self._message.identifier(cb.message),
            "message_chat_id": self._message.chat_id(cb.message),
            "message_thread_id": self._message.thread(cb.message),
            "message_chat_type": self._message.chat_type(cb.message),
            "user_id": self._user.identifier(cb.from_user),
            "user_language": self._user.language(cb.from_user),
            "user_username": self._user.username(cb.from_user),
            "user_first_name": self._user.first_name(cb.from_user),
            "user_last_name": self._user.last_name(cb.from_user),
        }
        return {key: value for key, value in metadata.items() if value is not None}


class RetreatEventFactory:
    """Create navigator back events using sanitized callback metadata."""

    def __init__(
        self, sanitizer: CallbackMetadataSanitizer | None = None
    ) -> None:
        self._sanitizer = sanitizer or CallbackMetadataSanitizer()

    def create(self, cb: CallbackQuery) -> NavigatorBackEvent:
        return NavigatorBackEvent(
            id=cb.id,
            data=cb.data,
            source="telegram",
            metadata=dict(self._sanitizer.sanitize(cb)),
        )


class RetreatContextBuilder:
    """Create navigator context payloads for retreat execution."""

    def __init__(self, event_factory: RetreatEventFactory | None = None) -> None:
        self._events = event_factory or RetreatEventFactory()

    def build(
        self, cb: CallbackQuery, payload: Mapping[str, object]
    ) -> NavigatorBackContext:
        """Return navigator back context augmented with sanitized event data."""

        context: MutableMapping[str, object] = dict(payload)
        return NavigatorBackContext(context, self._events.create(cb))


__all__ = [
    "CallbackMetadataSanitizer",
    "MessageMetadataExtractor",
    "RetreatContextBuilder",
    "RetreatEventFactory",
    "UserMetadataExtractor",
]

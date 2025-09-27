"""Context helpers for telegram retreat workflows."""

from __future__ import annotations

from typing import Mapping, MutableMapping

from aiogram.types import CallbackQuery, Message, User

from navigator.app.service.navigator_runtime.back_context import (
    NavigatorBackContext,
    NavigatorBackEvent,
)


class RetreatContextBuilder:
    """Create navigator context payloads for retreat execution."""

    def build(
        self, cb: CallbackQuery, payload: Mapping[str, object]
    ) -> NavigatorBackContext:
        """Return navigator back context augmented with sanitized event data."""

        context: MutableMapping[str, object] = dict(payload)
        return NavigatorBackContext(context, self._event(cb))

    def _event(self, cb: CallbackQuery) -> NavigatorBackEvent:
        return NavigatorBackEvent(
            id=cb.id,
            data=cb.data,
            inline_message_id=cb.inline_message_id,
            chat_instance=cb.chat_instance,
            message_id=self._message_id(cb.message),
            message_chat_id=self._message_chat(cb.message),
            message_thread_id=self._message_thread(cb.message),
            message_chat_type=self._message_chat_type(cb.message),
            user_id=self._user_id(cb.from_user),
            user_language=self._user_language(cb.from_user),
            user_username=self._user_username(cb.from_user),
            user_first_name=self._user_first_name(cb.from_user),
            user_last_name=self._user_last_name(cb.from_user),
        )

    @staticmethod
    def _message_id(message: Message | None) -> int | None:
        return getattr(message, "message_id", None)

    @staticmethod
    def _message_chat(message: Message | None) -> int | None:
        chat = getattr(message, "chat", None)
        return getattr(chat, "id", None)

    @staticmethod
    def _message_thread(message: Message | None) -> int | None:
        return getattr(message, "message_thread_id", None)

    @staticmethod
    def _message_chat_type(message: Message | None) -> str | None:
        chat = getattr(message, "chat", None)
        return getattr(chat, "type", None)

    @staticmethod
    def _user_id(user: User | None) -> int | None:
        return getattr(user, "id", None)

    @staticmethod
    def _user_language(user: User | None) -> str | None:
        code = getattr(user, "language_code", None)
        return str(code) if code is not None else None

    @staticmethod
    def _user_username(user: User | None) -> str | None:
        return getattr(user, "username", None)

    @staticmethod
    def _user_first_name(user: User | None) -> str | None:
        return getattr(user, "first_name", None)

    @staticmethod
    def _user_last_name(user: User | None) -> str | None:
        return getattr(user, "last_name", None)


__all__ = ["RetreatContextBuilder"]

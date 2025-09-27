"""Helpers for deriving Telegram message targets."""
from __future__ import annotations

from typing import Any, Dict, Optional

from navigator.core.value.message import Scope


def resolve_targets(
    scope: Scope,
    message: Optional[int] = None,
    *,
    topical: bool = True,
) -> Dict[str, Any]:
    """Build keyword arguments describing Telegram addressing semantics."""

    data: Dict[str, Any] = {}
    if scope.inline:
        data["inline_message_id"] = scope.inline
    elif scope.business:
        data["business_connection_id"] = scope.business
        if message is not None:
            data["message_id"] = message
    else:
        data["chat_id"] = scope.chat
        if message is not None:
            data["message_id"] = message
    if topical and not scope.inline and scope.topic is not None:
        if getattr(scope, "direct", False):
            data["direct_messages_topic_id"] = scope.topic
        else:
            data["message_thread_id"] = scope.topic
    return data


__all__ = ["resolve_targets"]

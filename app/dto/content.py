"""Define application-level DTOs for payload assembly."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...core.entity.markup import Markup
from ...core.value.content import Preview

Extra = Dict[str, Any]


@dataclass(frozen=True, slots=True)
class Media:
    """Represent media inputs captured from upstream adapters."""

    path: object
    type: Optional[str] = None
    caption: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Content:
    """Describe Navigator content transfer object contract.

    Extra payload notes:
    * ``message_effect_id`` applies only when targeting private chats.
    * Normalisation strips unsupported effects when editing existing content.
    * Updating only the effect without changing content does not trigger writes.

    Caption erasure rules:
    * ``media`` with ``erase=True`` and ``text`` in ``(None, "")`` clears captions.
    * ``media`` with an empty caption requires ``erase`` to be ``True``.
    """

    text: Optional[str] = None
    media: Optional[Media] = None
    group: Optional[List[Media]] = None
    reply: Optional[Markup] = None
    preview: Optional[Preview] = None
    extra: Optional[Extra] = None
    erase: bool = False


@dataclass(frozen=True, slots=True)
class Node:
    """Group sequential content messages for batch operations."""

    messages: List[Content]


__all__ = ["Content", "Media", "Node"]

"""Data structures used by rendering planner workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from navigator.core.entity.history import Message
from navigator.core.typing.result import Cluster, GroupMeta, MediaMeta, Meta, TextMeta

from ..executor import Execution


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Describe a single gateway result produced during rendering."""

    id: int
    extra: List[int]
    meta: Meta


@dataclass(frozen=True, slots=True)
class RenderNode:
    """Collect identifiers and metadata for a rendered node."""

    ids: List[int]
    extras: List[List[int]]
    metas: List[Meta]
    changed: bool


@dataclass(slots=True)
class RenderState:
    """Accumulate message identifiers and metadata during planning."""

    ids: List[int] = field(default_factory=list)
    extras: List[List[int]] = field(default_factory=list)
    metas: List[Meta] = field(default_factory=list)

    def retain(self, message: Message) -> None:
        """Record existing message details without triggering mutations."""

        self.ids.append(message.id)
        self.extras.append(list(message.extras or []))
        self.metas.append(_meta(message))

    def collect(self, execution: Execution, meta: Meta) -> None:
        """Capture execution outcome alongside calculated metadata."""

        self.ids.append(execution.result.id)
        self.extras.append(list(execution.result.extra))
        self.metas.append(meta)


def _meta(node: Message) -> Meta:
    """Convert stored history message into lightweight metadata."""

    if node.group:
        return GroupMeta(
            clusters=[
                Cluster(
                    medium=item.type.value,
                    file=item.path,
                    caption=item.caption,
                )
                for item in node.group
            ],
            inline=node.inline,
        )
    if node.media:
        return MediaMeta(
            medium=node.media.type.value,
            file=node.media.path,
            caption=node.media.caption,
            inline=node.inline,
        )
    return TextMeta(text=node.text, inline=node.inline)


__all__ = ["RenderNode", "RenderResult", "RenderState"]


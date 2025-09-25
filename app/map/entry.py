"""Convert rendering outcomes into persisted history entries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from ...core.entity.history import Entry, Message
from ...core.entity.media import MediaItem, MediaType
from ...core.error import (
    MetadataGroupMediumMissing,
    MetadataKindMissing,
    MetadataKindUnsupported,
    MetadataMediumMissing,
)
from ...core.port.factory import ViewLedger
from ...core.service.history.extra import cleanse
from ...core.typing.result import GroupMeta, MediaMeta, Meta, TextMeta
from ...core.value.content import Payload


def _previous_extra(
        base: Optional[Entry],
        index: int,
) -> Optional[dict[str, Any]]:
    """Return the previous message extra for ``index`` if available."""

    if base is None:
        return None
    messages = getattr(base, "messages", None) or []
    if index >= len(messages):
        return None
    return messages[index].extra


def _media_item_from_meta(meta: MediaMeta, payload: Payload) -> MediaItem:
    """Build a ``MediaItem`` using payload defaults when required."""

    variant = meta.medium
    if payload.media:
        return MediaItem(
            type=payload.media.type,
            path=meta.file,
            caption=meta.caption,
        )
    if isinstance(variant, str):
        return MediaItem(
            type=MediaType(variant),
            path=meta.file,
            caption=meta.caption,
        )
    raise MetadataMediumMissing()


def _group_items_from_meta(meta: GroupMeta) -> List[MediaItem]:
    """Return media items representing grouped content metadata."""

    items: List[MediaItem] = []
    for cluster in meta.clusters:
        variant = cluster.medium
        if not isinstance(variant, str):
            raise MetadataGroupMediumMissing()
        items.append(
            MediaItem(
                type=MediaType(variant),
                path=cluster.file,
                caption=cluster.caption,
            )
        )
    return items


def _message_content(
        meta: Meta,
        payload: Payload,
) -> Tuple[Optional[str], Optional[MediaItem], Optional[List[MediaItem]]]:
    """Return text, media, and group artefacts derived from ``meta``."""

    if isinstance(meta, TextMeta):
        return meta.text, None, None
    if isinstance(meta, MediaMeta):
        return None, _media_item_from_meta(meta, payload), None
    if isinstance(meta, GroupMeta):
        return None, None, _group_items_from_meta(meta)
    raise MetadataKindUnsupported(getattr(meta, "kind", None))


def _caption_length(
        text: Optional[str],
        media: Optional[MediaItem],
        group: Optional[Iterable[MediaItem]],
) -> int:
    """Return caption length for sanitising entity spans."""

    if group:
        first = next(iter(group), None)
        return len(getattr(first, "caption", None) or "") if first else 0
    if media:
        return len(getattr(media, "caption", None) or "")
    return len(text or "")


def _resolve_inline(meta: Meta) -> Optional[bool]:
    """Return inline flag derived from metadata if specified."""

    inline = getattr(meta, "inline", None)
    return bool(inline) if inline is not None else None


def _clean_extra(
        payload: Payload,
        base: Optional[Entry],
        index: int,
        length: int,
) -> Optional[dict[str, Any]]:
    """Return sanitised extra metadata for ``payload`` at ``index``."""

    source = payload.extra if payload.extra is not None else _previous_extra(base, index)
    return cleanse(source, length=length)


def _view_if_known(ledger: ViewLedger, view: Optional[str]) -> Optional[str]:
    """Return ``view`` only when the ledger recognises the identifier."""

    if view and ledger.has(view):
        return view
    return None


class EntryMapper:
    """Translate rendering outcomes into persisted history entries."""

    def __init__(self, ledger: ViewLedger):
        self._ledger = ledger

    def convert(
            self,
            outcome: "Outcome",
            payloads: List[Payload],
            state: Optional[str],
            view: Optional[str],
            root: bool,
            base: Optional[Entry] = None,
    ) -> Entry:
        """Build an entry from payloads and delivery outcome metadata."""

        now = datetime.now(timezone.utc)
        messages: List[Message] = []

        for index, payload in enumerate(payloads):
            meta = outcome.meta_at(index)
            inline = _resolve_inline(meta)
            text, media, group = _message_content(meta, payload)

            length = _caption_length(text, media, group)
            extra = _clean_extra(payload, base, index, length)

            messages.append(
                Message(
                    id=outcome.id_at(index),
                    text=text,
                    media=media,
                    group=group,
                    markup=payload.reply,
                    preview=payload.preview,
                    extra=extra,
                    extras=outcome.extras_at(index),
                    inline=inline,
                    automated=True,
                    ts=now,
                )
            )

        return Entry(
            state=state,
            view=_view_if_known(self._ledger, view),
            messages=messages,
            root=bool(root),
        )


class Outcome:
    """Provide convenient accessors around rendering outcome metadata."""

    def __init__(
            self,
            ids: Sequence[int],
            extras: Optional[Sequence[Sequence[int]]],
            metas: Sequence[Meta],
    ):
        self.ids = [int(identifier) for identifier in ids]
        self.extras = [list(extra) for extra in extras or []]
        self.metas = list(metas or [])

    def id_at(self, index: int) -> int:
        return self.ids[index]

    def extras_at(self, index: int) -> List[int]:
        if index < len(self.extras):
            return list(self.extras[index])
        return []

    def meta_at(self, index: int) -> Meta:
        if index >= len(self.metas):
            raise MetadataKindMissing()
        return self.metas[index]


__all__ = ["EntryMapper", "Outcome"]

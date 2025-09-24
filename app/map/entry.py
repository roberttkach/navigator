from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

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


class EntryMapper:
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
        """
        Преобразует отправленные payload'ы в Entry на основе детерминированных meta.
        В истории медиа и группы хранят Telegram file_id.
        """
        messages: List[Message] = []
        now = datetime.now(timezone.utc)
        for index, payload in enumerate(payloads):
            identifier = outcome.ids[index]
            meta = outcome.metas[index] if index < len(outcome.metas) else None
            if meta is None:
                raise MetadataKindMissing()
            inline = getattr(meta, "inline", None)

            previous = None
            if base and index < len(getattr(base, "messages", []) or []):
                try:
                    previous = base.messages[index].extra
                except Exception:
                    previous = None

            if isinstance(meta, TextMeta):
                text, media, group = meta.text, None, None
            elif isinstance(meta, MediaMeta):
                variant = meta.medium
                if payload.media:
                    mtype = payload.media.type
                elif isinstance(variant, str):
                    mtype = MediaType(variant)
                else:
                    raise MetadataMediumMissing()
                item = MediaItem(type=mtype, path=meta.file, caption=meta.caption)
                text, media, group = None, item, None
            elif isinstance(meta, GroupMeta):
                items = []
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
                text, media, group = None, None, items
            else:
                raise MetadataKindUnsupported(getattr(meta, "kind", None))

            source = payload.extra if (payload.extra is not None) else previous

            if group:
                first = group[0] if group else None
                length = len((getattr(first, "caption", None) or ""))
            elif media:
                length = len((getattr(media, "caption", None) or ""))
            elif isinstance(text, str) and not group and not media:
                length = len(text)
            else:
                length = 0

            extra = cleanse(source, length=length)
            auxiliary = outcome.extras[index] if index < len(outcome.extras) else []
            messages.append(
                Message(
                    id=identifier,
                    text=text,
                    media=media,
                    group=group,
                    markup=payload.reply,
                    preview=payload.preview,
                    extra=extra,
                    extras=list(auxiliary),
                    inline=inline,
                    automated=True,
                    ts=now,
                )
            )
        known = view if (view and self._ledger.has(view)) else None
        return Entry(state=state, view=known, messages=messages, root=bool(root))


class Outcome:
    def __init__(self, ids: List[int], extras: List[List[int]], metas: List[Meta]):
        self.ids = list(ids)
        self.extras = [list(x) for x in (extras or [])]
        self.metas = list(metas or [])


__all__ = ["EntryMapper", "Outcome"]

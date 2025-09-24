from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from ...domain.entity.history import Entry, Message
from ...domain.entity.media import MediaItem, MediaType
from ...domain.error import (
    MetadataGroupMediumMissing,
    MetadataKindMissing,
    MetadataKindUnsupported,
    MetadataMediumMissing,
)
from ...domain.port.factory import ViewLedger
from ...domain.service.history.extra import cleanse
from ...domain.value.content import Payload


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
            meta = outcome.metas[index] if index < len(outcome.metas) else {}
            k = meta.get("kind")
            if not isinstance(k, str):
                raise MetadataKindMissing()
            if k not in ("text", "media", "group"):
                raise MetadataKindUnsupported(k)
            inline = meta.get("inline")

            previous = None
            if base and index < len(getattr(base, "messages", []) or []):
                try:
                    previous = base.messages[index].extra
                except Exception:
                    previous = None

            if k == "text":
                text, media, group = meta.get("text"), None, None
            elif k == "media":
                variant = meta.get("medium")
                if payload.media:
                    mtype = payload.media.type
                elif isinstance(variant, str):
                    mtype = MediaType(variant)
                else:
                    raise MetadataMediumMissing()
                item = MediaItem(type=mtype, path=meta.get("file"), caption=meta.get("caption"))
                text, media, group = None, item, None
            elif k == "group":
                items = []
                for it in (meta.get("clusters") or []):
                    variant = it.get("medium")
                    if not isinstance(variant, str):
                        raise MetadataGroupMediumMissing()
                    items.append(
                        MediaItem(type=MediaType(variant), path=it.get("file"), caption=it.get("caption"))
                    )
                text, media, group = None, None, items

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
    def __init__(self, ids: List[int], extras: List[List[int]], metas: List[dict]):
        self.ids = list(ids)
        self.extras = [list(x) for x in (extras or [])]
        self.metas = [dict(m or {}) for m in (metas or [])]


__all__ = ["EntryMapper", "Outcome"]

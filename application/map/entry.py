from datetime import datetime, timezone
from typing import Optional, List

from ...domain.entity.history import Entry, Msg
from ...domain.entity.media import MediaItem, MediaType
from ...domain.port.factory import ViewFactoryRegistry
from ...domain.service.history.extra import cleanse
from ...domain.value.content import Payload


class EntryMapper:
    def __init__(self, registry: ViewFactoryRegistry):
        self._registry = registry

    def convert(
            self,
            result: "NodeResult",
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
        msgs: List[Msg] = []
        now = datetime.now(timezone.utc)
        for idx, payload in enumerate(payloads):
            mid = result.ids[idx]
            meta = result.metas[idx] if idx < len(result.metas) else {}
            k = meta.get("kind")
            if not isinstance(k, str):
                raise ValueError("meta_missing_kind")
            if k not in ("text", "media", "group"):
                raise ValueError(f"meta_unsupported_kind:{k}")
            inline = meta.get("inline_id")

            previous = None
            if base and idx < len(getattr(base, "messages", []) or []):
                try:
                    previous = base.messages[idx].extra
                except Exception:
                    previous = None

            if k == "text":
                text, media, group = meta.get("text"), None, None
            elif k == "media":
                variant = meta.get("media_type")
                if payload.media:
                    mtype = payload.media.type
                elif isinstance(variant, str):
                    mtype = MediaType(variant)
                else:
                    raise ValueError("meta_missing_media_type")
                mi = MediaItem(type=mtype, path=meta.get("file_id"), caption=meta.get("caption"))
                text, media, group = None, mi, None
            elif k == "group":
                items = []
                for it in (meta.get("group_items") or []):
                    variant = it.get("media_type")
                    if not isinstance(variant, str):
                        raise ValueError("meta_missing_group_media_type")
                    items.append(
                        MediaItem(type=MediaType(variant), path=it.get("file_id"), caption=it.get("caption"))
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
            aux = result.extras[idx] if idx < len(result.extras) else []
            msgs.append(
                Msg(
                    id=mid,
                    text=text,
                    media=media,
                    group=group,
                    markup=payload.reply,
                    preview=payload.preview,
                    extra=extra,
                    extras=list(aux),
                    inline_id=inline,
                    automated=True,
                    ts=now,
                )
            )
        vk = view if (view and self._registry.has(view)) else None
        return Entry(state=state, view=vk, messages=msgs, root=bool(root))


class NodeResult:
    def __init__(self, ids: List[int], extras: List[List[int]], metas: List[dict]):
        self.ids = list(ids)
        self.extras = [list(x) for x in (extras or [])]
        self.metas = [dict(m or {}) for m in (metas or [])]


__all__ = ["EntryMapper", "NodeResult"]

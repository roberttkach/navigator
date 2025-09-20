from datetime import datetime, timezone
from typing import Optional, List

from ...domain.entity.history import Entry, Msg
from ...domain.entity.media import MediaItem, MediaType
from ...domain.port.factory import ViewFactoryRegistry
from ...domain.value.content import Payload


class EntryMapper:
    def __init__(self, registry: ViewFactoryRegistry):
        self._registry = registry

    def from_node_result(
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
            inline_id = meta.get("inline_id")

            prev_extra = None
            if base and idx < len(getattr(base, "messages", []) or []):
                try:
                    prev_extra = base.messages[idx].extra
                except Exception:
                    prev_extra = None

            if k == "text":
                text, media, group = meta.get("text"), None, None
                extra = payload.extra if (payload.extra is not None) else prev_extra
            elif k == "media":
                mt_raw = meta.get("media_type")
                if payload.media:
                    mtype = payload.media.type
                elif isinstance(mt_raw, str):
                    mtype = MediaType(mt_raw)
                else:
                    raise ValueError("meta_missing_media_type")
                mi = MediaItem(type=mtype, path=meta.get("file_id"), caption=meta.get("caption"))
                text, media, group = None, mi, None
                extra = payload.extra if (payload.extra is not None) else prev_extra
            elif k == "group":
                items = []
                for it in (meta.get("group_items") or []):
                    mt_raw = it.get("media_type")
                    if not isinstance(mt_raw, str):
                        raise ValueError("meta_missing_group_media_type")
                    items.append(
                        MediaItem(type=MediaType(mt_raw), path=it.get("file_id"), caption=it.get("caption"))
                    )
                text, media, group = None, None, items
                extra = payload.extra if (payload.extra is not None) else prev_extra
            else:
                # Fallback: считать текстом
                text, media, group = payload.text, None, None
                extra = payload.extra if (payload.extra is not None) else prev_extra
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
                    aux_ids=list(aux),
                    inline_id=inline_id,
                    by_bot=True,
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

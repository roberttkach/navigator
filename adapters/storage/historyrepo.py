import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from aiogram.fsm.context import FSMContext

from .keys import FSM_HISTORY_KEY
from ...domain.entity.history import Entry, Msg
from ...domain.entity.markup import Markup
from ...domain.entity.media import MediaItem, MediaType
from ...domain.log.emit import jlog
from ...domain.value.content import Preview
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def _to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


class HistoryRepo:
    def __init__(self, state: FSMContext):
        self._state = state

    async def get_history(self) -> List[Entry]:
        data = await self._state.get_data()
        raw = data.get(FSM_HISTORY_KEY, [])
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": len(raw)})
        return [self._from_dict(d) for d in raw]

    async def save_history(self, history: List[Entry]) -> None:
        payload = [self._to_dict(entry) for entry in history]
        await self._state.update_data({FSM_HISTORY_KEY: payload})
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, history={"len": len(payload)})

    @staticmethod
    def _encode_media(item: Optional[MediaItem]) -> Optional[Dict[str, Any]]:
        if not item:
            return None
        return {
            "type": item.type.value,
            "file_id": item.path,
            "caption": item.caption,
        }

    @staticmethod
    def _decode_media(data: Any) -> Optional[MediaItem]:
        if not isinstance(data, Dict):
            return None
        t = data.get("type")
        f = data.get("file_id")
        if not (isinstance(t, str) and isinstance(f, str) and f):
            return None
        return MediaItem(type=MediaType(t), path=f, caption=data.get("caption"))

    @staticmethod
    def _encode_group(items: Optional[List[MediaItem]]) -> Optional[List[Dict[str, Any]]]:
        if not items:
            return None
        out = []
        for i in items:
            out.append(
                {
                    "type": i.type.value,
                    "file_id": i.path,
                    "caption": i.caption,
                }
            )
        return out

    @staticmethod
    def _decode_group(items: Any) -> Optional[List[MediaItem]]:
        if not isinstance(items, list):
            return None
        out: List[MediaItem] = []
        for it in items:
            if not isinstance(it, Dict):
                continue
            t = it.get("type")
            f = it.get("file_id")
            if not (isinstance(t, str) and isinstance(f, str) and f):
                continue
            out.append(MediaItem(type=MediaType(t), path=f, caption=it.get("caption")))
        return out or None

    @staticmethod
    def _encode_reply(rm: Optional[Markup]) -> Optional[Dict[str, Any]]:
        if not rm:
            return None
        return {"kind": rm.kind, "data": rm.data}

    @staticmethod
    def _decode_reply(data: Any) -> Optional[Markup]:
        if not isinstance(data, Dict):
            return None
        k = data.get("kind")
        dd = data.get("data")
        if isinstance(k, str) and isinstance(dd, dict):
            return Markup(kind=k, data=dd)
        return None

    @staticmethod
    def _encode_preview(p: Optional[Preview]) -> Optional[Dict[str, Any]]:
        if not p:
            return None
        return {
            "url": p.url,
            "small": p.small,
            "large": p.large,
            "above": p.above,
            "disabled": p.disabled,
        }

    @staticmethod
    def _decode_preview(p: Any) -> Optional[Preview]:
        if not isinstance(p, Dict):
            return None
        return Preview(
            url=p.get("url"),
            small=bool(p.get("small", False)),
            large=bool(p.get("large", False)),
            above=bool(p.get("above", False)),
            disabled=p.get("disabled"),
        )

    @staticmethod
    def _encode_dt(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def _decode_dt(raw: Any) -> datetime:
        if isinstance(raw, str):
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if getattr(dt, "tzinfo", None):
                    return dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        jlog(
            logger,
            logging.WARNING,
            LogCode.HISTORY_LOAD,
            note="ts_parse_failed_fallback_now",
            raw=(str(raw)[:64] if raw is not None else None),
        )
        return datetime.now(timezone.utc)

    def _to_dict(self, entry: Entry) -> Dict[str, Any]:
        return {
            "state": entry.state,
            "view": entry.view,
            "root": bool(getattr(entry, "root", False)),
            "messages": [
                {
                    "id": m.id,
                    "text": m.text,
                    "media": self._encode_media(m.media),
                    "group": self._encode_group(m.group),
                    "markup": self._encode_reply(m.markup),
                    "preview": self._encode_preview(m.preview),
                    "extra": m.extra,
                    "extras": list(m.extras),
                    "inline_id": m.inline_id,
                    "automated": m.automated,
                    "ts": self._encode_dt(m.ts),
                }
                for m in entry.messages
            ],
        }

    def _from_dict(self, data: Dict[str, Any]) -> Entry:
        msgs = data.get("messages")
        root_flag = bool(data.get("root", False))
        if isinstance(msgs, list) and not msgs:
            return Entry(
                state=data.get("state"),
                view=data.get("view"),
                messages=[],
                root=root_flag,
            )
        if isinstance(msgs, list):
            messages: List[Msg] = []
            for d in msgs:
                if not isinstance(d, Dict):
                    continue
                messages.append(
                    Msg(
                        id=_to_int(d.get("id"), 0),
                        text=d.get("text"),
                        media=self._decode_media(d.get("media")),
                        group=self._decode_group(d.get("group")),
                        markup=self._decode_reply(d.get("markup")),
                        preview=self._decode_preview(d.get("preview")),
                        extra=d.get("extra"),
                        extras=[
                            int(x)
                            for x in (
                                d.get("extras")
                                if d.get("extras") is not None
                                else d.get("aux_ids")
                                or []
                            )
                        ],
                        inline_id=d.get("inline_id"),
                        automated=bool(
                            d.get(
                                "automated",
                                d.get("by_bot", True),
                            )
                        ),
                        ts=self._decode_dt(d.get("ts")),
                    )
                )
            return Entry(
                state=data.get("state"),
                view=data.get("view"),
                messages=messages,
                root=root_flag,
            )
        return Entry(
            state=data.get("state"),
            view=data.get("view"),
            messages=[],
            root=root_flag,
        )

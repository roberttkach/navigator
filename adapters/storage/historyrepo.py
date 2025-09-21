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


def _integral(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


class MediaCodec:
    @staticmethod
    def pack(item: Optional[MediaItem]) -> Optional[Dict[str, Any]]:
        if not item:
            return None
        return {
            "type": item.type.value,
            "file_id": item.path,
            "caption": item.caption,
        }

    @staticmethod
    def unpack(data: Any) -> Optional[MediaItem]:
        if not isinstance(data, Dict):
            return None
        kind = data.get("type")
        file_id = data.get("file_id")
        if not (isinstance(kind, str) and isinstance(file_id, str) and file_id):
            return None
        return MediaItem(type=MediaType(kind), path=file_id, caption=data.get("caption"))


class GroupCodec:
    @staticmethod
    def pack(items: Optional[List[MediaItem]]) -> Optional[List[Dict[str, Any]]]:
        if not items:
            return None
        packed: List[Dict[str, Any]] = []
        for item in items:
            encoded = MediaCodec.pack(item)
            if encoded is not None:
                packed.append(encoded)
        return packed or None

    @staticmethod
    def unpack(items: Any) -> Optional[List[MediaItem]]:
        if not isinstance(items, list):
            return None
        out: List[MediaItem] = []
        for raw in items:
            media = MediaCodec.unpack(raw)
            if media is not None:
                out.append(media)
        return out or None


class ReplyCodec:
    @staticmethod
    def pack(rm: Optional[Markup]) -> Optional[Dict[str, Any]]:
        if not rm:
            return None
        return {"kind": rm.kind, "data": rm.data}

    @staticmethod
    def unpack(data: Any) -> Optional[Markup]:
        if not isinstance(data, Dict):
            return None
        kind = data.get("kind")
        payload = data.get("data")
        if isinstance(kind, str) and isinstance(payload, dict):
            return Markup(kind=kind, data=payload)
        return None


class PreviewCodec:
    @staticmethod
    def pack(p: Optional[Preview]) -> Optional[Dict[str, Any]]:
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
    def unpack(p: Any) -> Optional[Preview]:
        if not isinstance(p, Dict):
            return None
        return Preview(
            url=p.get("url"),
            small=bool(p.get("small", False)),
            large=bool(p.get("large", False)),
            above=bool(p.get("above", False)),
            disabled=p.get("disabled"),
        )


class TimeCodec:
    @staticmethod
    def pack(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def unpack(raw: Any) -> datetime:
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


class HistoryRepo:
    def __init__(self, state: FSMContext):
        self._state = state

    async def recall(self) -> List[Entry]:
        data = await self._state.get_data()
        raw = data.get(FSM_HISTORY_KEY, [])
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": len(raw)})
        return [self._load(d) for d in raw]

    async def archive(self, history: List[Entry]) -> None:
        payload = [self._dump(entry) for entry in history]
        await self._state.update_data({FSM_HISTORY_KEY: payload})
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, history={"len": len(payload)})

    def _dump(self, entry: Entry) -> Dict[str, Any]:
        return {
            "state": entry.state,
            "view": entry.view,
            "root": bool(getattr(entry, "root", False)),
            "messages": [
                {
                    "id": m.id,
                    "text": m.text,
                    "media": MediaCodec.pack(m.media),
                    "group": GroupCodec.pack(m.group),
                    "markup": ReplyCodec.pack(m.markup),
                    "preview": PreviewCodec.pack(m.preview),
                    "extra": m.extra,
                    "extras": list(m.extras),
                    "inline": m.inline,
                    "automated": m.automated,
                    "ts": TimeCodec.pack(m.ts),
                }
                for m in entry.messages
            ],
        }

    def _load(self, data: Dict[str, Any]) -> Entry:
        msgs = data.get("messages")
        rootmark = bool(data.get("root", False))
        if isinstance(msgs, list) and not msgs:
            return Entry(
                state=data.get("state"),
                view=data.get("view"),
                messages=[],
                root=rootmark,
            )
        if isinstance(msgs, list):
            messages: List[Msg] = []
            for d in msgs:
                if not isinstance(d, Dict):
                    continue

                legacy = {"aux_ids", "inline_id", "by_bot"}.intersection(d.keys())
                if legacy:
                    jlog(
                        logger,
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="legacy_history_message",
                        keys=sorted(legacy),
                    )
                    raise ValueError(
                        "Legacy history payload keys are no longer supported: "
                        + ", ".join(sorted(legacy))
                    )

                if "automated" not in d:
                    jlog(
                        logger,
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_missing_automated",
                    )
                    raise ValueError("History message payload missing required 'automated' flag")

                messages.append(
                    Msg(
                        id=_integral(d.get("id"), 0),
                        text=d.get("text"),
                        media=MediaCodec.unpack(d.get("media")),
                        group=GroupCodec.unpack(d.get("group")),
                        markup=ReplyCodec.unpack(d.get("markup")),
                        preview=PreviewCodec.unpack(d.get("preview")),
                        extra=d.get("extra"),
                        extras=[int(x) for x in (d.get("extras") or [])],
                        inline=d.get("inline"),
                        automated=bool(d.get("automated")),
                        ts=TimeCodec.unpack(d.get("ts")),
                    )
                )
            return Entry(
                state=data.get("state"),
                view=data.get("view"),
                messages=messages,
                root=rootmark,
            )
        return Entry(
            state=data.get("state"),
            view=data.get("view"),
            messages=[],
            root=rootmark,
        )

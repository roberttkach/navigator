import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from aiogram.fsm.context import FSMContext

from .keys import FSM_HISTORY_KEY
from navigator.domain.entity.history import Entry, Message
from navigator.domain.entity.markup import Markup
from navigator.domain.entity.media import MediaItem, MediaType
from navigator.domain.value.content import Preview
from navigator.logging import LogCode, jlog

logger = logging.getLogger(__name__)


class MediaCodec:
    @staticmethod
    def pack(item: Optional[MediaItem]) -> Optional[Dict[str, Any]]:
        if not item:
            return None
        return {
            "type": item.type.value,
            "file": item.path,
            "caption": item.caption,
        }

    @staticmethod
    def unpack(data: Any) -> Optional[MediaItem]:
        if not isinstance(data, Dict):
            return None
        kind = data.get("type")
        identifier = data.get("file")
        if not (isinstance(kind, str) and isinstance(identifier, str) and identifier):
            return None
        return MediaItem(type=MediaType(kind), path=identifier, caption=data.get("caption"))


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
            except Exception as exc:
                jlog(
                    logger,
                    logging.ERROR,
                    LogCode.HISTORY_LOAD,
                    note="history_message_invalid_ts",
                    raw=raw[:64],
                )
                raise ValueError(f"History message payload has invalid 'ts': {raw!r}") from exc
        jlog(
            logger,
            logging.ERROR,
            LogCode.HISTORY_LOAD,
            note="history_message_invalid_ts",
            raw=(str(raw)[:64] if raw is not None else None),
        )
        raise ValueError(
            "History message payload has invalid 'ts': "
            f"{raw!r} (type {type(raw).__name__})"
        )


class Chronicle:
    def __init__(self, state: FSMContext):
        self._state = state

    async def recall(self) -> List[Entry]:
        data = await self._state.get_data()
        raw = data.get(FSM_HISTORY_KEY, [])
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": len(raw)})
        return [self._load(record) for record in raw]

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
                    "id": message.id,
                    "text": message.text,
                    "media": MediaCodec.pack(message.media),
                    "group": GroupCodec.pack(message.group),
                    "markup": ReplyCodec.pack(message.markup),
                    "preview": PreviewCodec.pack(message.preview),
                    "extra": message.extra,
                    "extras": list(message.extras),
                    "inline": message.inline,
                    "automated": message.automated,
                    "ts": TimeCodec.pack(message.ts),
                }
                for message in entry.messages
            ],
        }

    def _load(self, data: Dict[str, Any]) -> Entry:
        items = data.get("messages")
        rootmark = bool(data.get("root", False))
        if isinstance(items, list) and not items:
            return Entry(
                state=data.get("state"),
                view=data.get("view"),
                messages=[],
                root=rootmark,
            )
        if isinstance(items, list):
            messages: List[Message] = []
            for record in items:
                if not isinstance(record, Dict):
                    continue

                if "automated" not in record:
                    jlog(
                        logger,
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_missing_automated",
                    )
                    raise ValueError("History message payload missing required 'automated' flag")

                if "id" not in record:
                    jlog(
                        logger,
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_missing_id",
                    )
                    raise ValueError("History message payload missing required 'id'")

                raw = record.get("id")
                try:
                    ident = int(raw)
                except (TypeError, ValueError):
                    jlog(
                        logger,
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_invalid_id",
                        raw=raw,
                    )
                    raise ValueError(f"History message payload has invalid 'id': {raw!r}")

                source = record.get("extras") or []
                extras: List[int] = []
                for value in source:
                    if not isinstance(value, int):
                        jlog(
                            logger,
                            logging.ERROR,
                            LogCode.HISTORY_LOAD,
                            note="history_message_invalid_extra",
                            raw=value,
                        )
                        raise ValueError(
                            "History message payload has non-integer 'extras' entry: "
                            f"{value!r} (type {type(value).__name__})"
                        )
                    extras.append(value)

                messages.append(
                    Message(
                        id=ident,
                        text=record.get("text"),
                        media=MediaCodec.unpack(record.get("media")),
                        group=GroupCodec.unpack(record.get("group")),
                        markup=ReplyCodec.unpack(record.get("markup")),
                        preview=PreviewCodec.unpack(record.get("preview")),
                        extra=record.get("extra"),
                        extras=extras,
                        inline=record.get("inline"),
                        automated=bool(record.get("automated")),
                        ts=TimeCodec.unpack(record.get("ts")),
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


__all__ = ["Chronicle"]

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from aiogram.fsm.context import FSMContext

from navigator.domain.entity.history import Entry, Message
from navigator.log import LogCode, jlog

from ..codec import GroupCodec, MediaCodec, PreviewCodec, ReplyCodec, TimeCodec
from .keys import FSM_HISTORY_KEY

logger = logging.getLogger(__name__)


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

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from aiogram.fsm.context import FSMContext

from navigator.core.entity.history import Entry, Message
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel

from ..codec import GroupCodec, MediaCodec, PreviewCodec, ReplyCodec, TimeCodec
from .keys import FSM_HISTORY_FIELD, FSM_NAMESPACE_KEY

class Chronicle:
    def __init__(self, state: FSMContext, telemetry: Telemetry | None = None):
        self._state = state
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )
        self._time = TimeCodec(telemetry)

    def _emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    async def recall(self) -> List[Entry]:
        data = await self._state.get_data()
        namespace = data.get(FSM_NAMESPACE_KEY) or {}
        raw = namespace.get(FSM_HISTORY_FIELD, []) if isinstance(namespace, dict) else []
        self._emit(logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": len(raw)})
        return [self._load(record) for record in raw]

    async def archive(self, history: List[Entry]) -> None:
        payload = [self._dump(entry) for entry in history]
        data = await self._state.get_data()
        namespace = dict(data.get(FSM_NAMESPACE_KEY) or {})
        namespace[FSM_HISTORY_FIELD] = payload
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace})
        self._emit(logging.DEBUG, LogCode.HISTORY_SAVE, history={"len": len(payload)})

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
                    self._emit(
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_missing_automated",
                    )
                    raise ValueError("History message payload missing required 'automated' flag")

                if "id" not in record:
                    self._emit(
                        logging.ERROR,
                        LogCode.HISTORY_LOAD,
                        note="history_message_missing_id",
                    )
                    raise ValueError("History message payload missing required 'id'")

                raw = record.get("id")
                try:
                    ident = int(raw)
                except (TypeError, ValueError):
                    self._emit(
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
                        self._emit(
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
                        ts=self._time.unpack(record.get("ts")),
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

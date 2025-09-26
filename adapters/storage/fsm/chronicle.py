from __future__ import annotations

import logging
from navigator.core.entity.history import Entry, Message
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Any, Dict, List

from .keys import FSM_HISTORY_FIELD, FSM_NAMESPACE_KEY
from ..codec import GroupCodec, MediaCodec, PreviewCodec, ReplyCodec, TimeCodec
from .context import StateContext


class Chronicle:
    def __init__(self, state: StateContext, telemetry: Telemetry | None = None):
        self._state = state
        self._telemetry = _TelemetryEmitter(telemetry)
        self._serializer = _HistorySerializer(telemetry)

    async def recall(self) -> List[Entry]:
        data = await self._state.get_data()
        namespace = self._namespace(data)
        raw = namespace.get(FSM_HISTORY_FIELD, [])
        self._telemetry.loaded(len(raw))
        return [
            self._serializer.load(record, self._telemetry)
            for record in raw
            if isinstance(record, dict)
        ]

    async def archive(self, history: List[Entry]) -> None:
        payload = [self._serializer.dump(entry) for entry in history]
        data = await self._state.get_data()
        namespace = dict(self._namespace(data))
        namespace[FSM_HISTORY_FIELD] = payload
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace})
        self._telemetry.saved(len(payload))

    @staticmethod
    def _namespace(data: Dict[str, Any]) -> Dict[str, Any]:
        namespace = data.get(FSM_NAMESPACE_KEY)
        return namespace if isinstance(namespace, dict) else {}


class _TelemetryEmitter:
    def __init__(self, telemetry: Telemetry | None) -> None:
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    def loaded(self, length: int) -> None:
        self.emit(logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": length})

    def saved(self, length: int) -> None:
        self.emit(logging.DEBUG, LogCode.HISTORY_SAVE, history={"len": length})

    def error(self, note: str, **fields: Any) -> None:
        self.emit(logging.ERROR, LogCode.HISTORY_LOAD, note=note, **fields)


class _HistorySerializer:
    def __init__(self, telemetry: Telemetry | None) -> None:
        self._time = TimeCodec(telemetry)

    def dump(self, entry: Entry) -> Dict[str, Any]:
        return {
            "state": entry.state,
            "view": entry.view,
            "root": bool(getattr(entry, "root", False)),
            "messages": [self._dump_message(message) for message in entry.messages],
        }

    def load(self, data: Dict[str, Any], telemetry: _TelemetryEmitter) -> Entry:
        items = data.get("messages")
        rootmark = bool(data.get("root", False))
        if isinstance(items, list):
            messages = [
                self._load_message(record, telemetry)
                for record in items
                if isinstance(record, dict)
            ]
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

    def _dump_message(self, message: Message) -> Dict[str, Any]:
        return {
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

    def _load_message(self, record: Dict[str, Any], telemetry: _TelemetryEmitter) -> Message:
        automated = self._require(
            record,
            "automated",
            telemetry,
            "history_message_missing_automated",
            message="History message payload missing required 'automated' flag",
        )
        raw_id = self._require(record, "id", telemetry, "history_message_missing_id")
        ident = self._parse_identifier(raw_id, telemetry)
        extras = self._parse_extras(record.get("extras"), telemetry)
        return Message(
            id=ident,
            text=record.get("text"),
            media=MediaCodec.unpack(record.get("media")),
            group=GroupCodec.unpack(record.get("group")),
            markup=ReplyCodec.unpack(record.get("markup")),
            preview=PreviewCodec.unpack(record.get("preview")),
            extra=record.get("extra"),
            extras=extras,
            inline=record.get("inline"),
            automated=bool(automated),
            ts=self._time.unpack(record.get("ts")),
        )

    def _require(
            self,
            record: Dict[str, Any],
            key: str,
            telemetry: _TelemetryEmitter,
            note: str,
            *,
            message: str | None = None,
    ) -> Any:
        if key not in record:
            telemetry.error(note)
            detail = message or f"History message payload missing required '{key}'"
            raise ValueError(detail)
        return record.get(key)

    def _parse_identifier(self, raw: Any, telemetry: _TelemetryEmitter) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError):
            telemetry.error("history_message_invalid_id", raw=raw)
            raise ValueError(f"History message payload has invalid 'id': {raw!r}")

    def _parse_extras(self, values: Any, telemetry: _TelemetryEmitter) -> List[int]:
        extras: List[int] = []
        for value in values or []:
            if not isinstance(value, int):
                telemetry.error("history_message_invalid_extra", raw=value)
                raise ValueError(
                    "History message payload has non-integer 'extras' entry: "
                    f"{value!r} (type {type(value).__name__})"
                )
            extras.append(value)
        return extras


__all__ = ["Chronicle"]

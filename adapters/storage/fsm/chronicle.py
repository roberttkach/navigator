from __future__ import annotations

import logging
from navigator.core.entity.history import Entry, Message
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

from .keys import FSM_HISTORY_FIELD, FSM_NAMESPACE_KEY
from ..codec import GroupCodec, MediaCodec, PreviewCodec, ReplyCodec, TimeCodec
from .context import StateContext


class Chronicle:
    def __init__(
        self,
        state: StateContext,
        telemetry: Telemetry | None = None,
        *,
        storage: "ChronicleStorage" | None = None,
        serializer: "HistorySerializer" | None = None,
        emitter: "ChronicleTelemetry" | None = None,
    ) -> None:
        self._storage = storage or ChronicleStorage(state)
        self._telemetry = emitter or ChronicleTelemetry(telemetry)
        self._serializer = serializer or HistorySerializer(telemetry)

    async def recall(self) -> List[Entry]:
        namespace = await self._storage.read()
        raw = namespace.history()
        self._telemetry.loaded(len(raw))
        return [
            self._serializer.load(record, self._telemetry)
            for record in raw
            if isinstance(record, dict)
        ]

    async def archive(self, history: List[Entry]) -> None:
        payload = [self._serializer.dump(entry) for entry in history]
        namespace = await self._storage.read()
        namespace.update_history(payload)
        await self._storage.write(namespace)
        self._telemetry.saved(len(payload))


class ChronicleStorage:
    """Persist FSM chronicle namespaces in the underlying state context."""

    def __init__(self, state: StateContext) -> None:
        self._state = state

    async def read(self) -> "ChronicleNamespace":
        data = await self._state.get_data()
        namespace = data.get(FSM_NAMESPACE_KEY)
        payload = namespace if isinstance(namespace, dict) else {}
        return ChronicleNamespace(payload)

    async def write(self, namespace: "ChronicleNamespace") -> None:
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace.dump()})


class ChronicleNamespace:
    """Access helpers around FSM namespace payloads."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload: MutableMapping[str, Any] = dict(payload)

    def history(self) -> List[Mapping[str, Any]]:
        raw = self._payload.get(FSM_HISTORY_FIELD, [])
        return raw if isinstance(raw, list) else []

    def update_history(self, history: Iterable[Mapping[str, Any]]) -> None:
        self._payload[FSM_HISTORY_FIELD] = list(history)

    def dump(self) -> Dict[str, Any]:
        return dict(self._payload)


class ChronicleTelemetry:
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


class HistorySerializer:
    def __init__(self, telemetry: Telemetry | None) -> None:
        self._time = TimeCodec(telemetry)

    def dump(self, entry: Entry) -> Dict[str, Any]:
        return {
            "state": entry.state,
            "view": entry.view,
            "root": bool(getattr(entry, "root", False)),
            "messages": [self._dump_message(message) for message in entry.messages],
        }

    def load(self, data: Dict[str, Any], telemetry: ChronicleTelemetry) -> Entry:
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

    def _load_message(self, record: Dict[str, Any], telemetry: ChronicleTelemetry) -> Message:
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
            telemetry: ChronicleTelemetry,
            note: str,
            *,
            message: str | None = None,
    ) -> Any:
        if key not in record:
            telemetry.error(note)
            detail = message or f"History message payload missing required '{key}'"
            raise ValueError(detail)
        return record.get(key)

    def _parse_identifier(self, raw: Any, telemetry: ChronicleTelemetry) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError):
            telemetry.error("history_message_invalid_id", raw=raw)
            raise ValueError(f"History message payload has invalid 'id': {raw!r}")

    def _parse_extras(self, values: Any, telemetry: ChronicleTelemetry) -> List[int]:
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

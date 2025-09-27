"""Serialisation helpers used by chronicle storage."""
from __future__ import annotations

from typing import Any, Dict, List

from navigator.core.entity.history import Entry, Message
from navigator.core.telemetry import Telemetry

from ..codec import GroupCodec, MediaCodec, PreviewCodec, ReplyCodec, TimeCodec
from .chronicle_telemetry import ChronicleTelemetry


class HistorySerializer:
    """Serialise and deserialise history entries for chronicle storage."""

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


__all__ = ["HistorySerializer"]

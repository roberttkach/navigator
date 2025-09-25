"""Convert between aiogram keyboard objects and Navigator markup."""

from __future__ import annotations

import logging
from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from navigator.core.entity.markup import Markup
from navigator.core.port.markup import MarkupCodec
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Any, Optional, Type

_AIROGRAM_TYPES: dict[str, Type[Any]] = {
    "InlineKeyboardMarkup": InlineKeyboardMarkup,
    "ReplyKeyboardMarkup": ReplyKeyboardMarkup,
    "ReplyKeyboardRemove": ReplyKeyboardRemove,
    "ForceReply": ForceReply,
}


class AiogramCodec(MarkupCodec):
    """Bridge aiogram keyboard objects with Navigator markup entities."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def encode(self, markup: Any) -> Optional[Markup]:
        """Translate aiogram markup objects into serialisable structures."""

        if not markup:
            self._emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False)
            return None
        kind = markup.__class__.__name__
        target = _AIROGRAM_TYPES.get(kind)
        if target is None:
            self._emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False, kind=kind)
            return None
        self._emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=True, kind=kind)
        return Markup(
            kind=kind,
            data=markup.model_dump(exclude_none=True, by_alias=True),
        )

    def decode(self, stored: Optional[Markup]) -> Any:
        """Reconstruct aiogram markup objects from stored metadata."""

        if not stored:
            return None
        target = _AIROGRAM_TYPES.get(stored.kind)
        if target is None:
            self._emit(logging.DEBUG, LogCode.MARKUP_DECODE, recognized=False, kind=stored.kind)
            return None
        try:
            result = target.model_validate(stored.data)
        except Exception:
            self._emit(
                logging.WARNING,
                LogCode.MARKUP_DECODE,
                recognized=False,
                kind=stored.kind,
                note="type_error",
            )
            return None
        self._emit(logging.DEBUG, LogCode.MARKUP_DECODE, recognized=True, kind=stored.kind)
        return result

    def _emit(self, level: int, code: LogCode, **fields: Any) -> None:
        """Emit telemetry events only when a channel is available."""

        self._channel.emit(level, code, **fields)


__all__ = ["AiogramCodec"]

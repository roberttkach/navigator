import logging
from typing import Optional, Any

from aiogram.types import (
    InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
)

from navigator.core.entity.markup import Markup
from navigator.core.port.markup import MarkupCodec
from navigator.core.telemetry import LogCode, telemetry

channel = telemetry.channel(__name__)


class AiogramCodec(MarkupCodec):
    _MAP = {
        "InlineKeyboardMarkup": InlineKeyboardMarkup,
        "ReplyKeyboardMarkup": ReplyKeyboardMarkup,
        "ReplyKeyboardRemove": ReplyKeyboardRemove,
        "ForceReply": ForceReply,
    }

    def encode(self, markup: Any) -> Optional[Markup]:
        if not markup:
            channel.emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False)
            return None
        kind = markup.__class__.__name__
        if kind in self._MAP:
            channel.emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=True, kind=kind)
            return Markup(
                kind=kind,
                data=markup.model_dump(exclude_none=True, by_alias=True)
            )
        channel.emit(logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False, kind=kind)
        return None

    def decode(self, stored: Optional[Markup]) -> Any:
        if not stored:
            return None
        target = self._MAP.get(stored.kind)
        if target:
            try:
                obj = target(**stored.data)
                channel.emit(logging.DEBUG, LogCode.MARKUP_DECODE, recognized=True, kind=stored.kind)
                return obj
            except TypeError:
                channel.emit(
                    logging.WARNING,
                    LogCode.MARKUP_DECODE,
                    recognized=False,
                    kind=stored.kind,
                    note="type_error",
                )
                return None
        channel.emit(logging.DEBUG, LogCode.MARKUP_DECODE, recognized=False, kind=stored.kind)
        return None


__all__ = ["AiogramCodec"]

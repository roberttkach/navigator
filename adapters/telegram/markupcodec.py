import logging
from typing import Optional, Any

from aiogram.types import (
    InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
)

from ...domain.entity.markup import Markup
from ...domain.log.emit import jlog
from ...domain.port.markup import MarkupCodec
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class AiogramMarkupCodec(MarkupCodec):
    _MAP = {
        "InlineKeyboardMarkup": InlineKeyboardMarkup,
        "ReplyKeyboardMarkup": ReplyKeyboardMarkup,
        "ReplyKeyboardRemove": ReplyKeyboardRemove,
        "ForceReply": ForceReply,
    }

    def encode(self, markup: Any) -> Optional[Markup]:
        if not markup:
            jlog(logger, logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False)
            return None
        kind = markup.__class__.__name__
        if kind in self._MAP:
            jlog(logger, logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=True, kind=kind)
            return Markup(
                kind=kind,
                data=markup.model_dump(exclude_none=True, by_alias=True)
            )
        jlog(logger, logging.DEBUG, LogCode.MARKUP_ENCODE, recognized=False, kind=kind)
        return None

    def decode(self, stored: Optional[Markup]) -> Any:
        if not stored:
            return None
        target = self._MAP.get(stored.kind)
        if target:
            try:
                obj = target(**stored.data)
                jlog(logger, logging.DEBUG, LogCode.MARKUP_DECODE, recognized=True, kind=stored.kind)
                return obj
            except TypeError:
                jlog(logger, logging.WARNING, LogCode.MARKUP_DECODE, recognized=False, kind=stored.kind,
                     note="type_error")
                return None
        jlog(logger, logging.DEBUG, LogCode.MARKUP_DECODE, recognized=False, kind=stored.kind)
        return None


__all__ = ["AiogramMarkupCodec"]

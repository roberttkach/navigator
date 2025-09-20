import logging

from aiogram.types import InlineKeyboardMarkup

from .util import extract_meta
from .. import serializer
from ....domain.log.emit import jlog
from ....domain.port.message import Result
from ....domain.service.rendering.helpers import payload_kind
from ....domain.service.scope import scope_kv
from ....logging.code import LogCode

logger = logging.getLogger(__name__)


def reply_for_send(codec, scope, reply):
    obj = serializer.decode_reply(codec, reply)
    if obj is None:
        return None
    if bool(scope.biz_id):
        return obj if isinstance(obj, InlineKeyboardMarkup) else None
    ct = getattr(scope, "chat_kind", None)
    if ct == "private":
        return obj  # приватные чаты: разрешить все поддерживаемые reply-объекты
    if ct == "group":
        return obj  # группы: разрешить все поддерживаемые reply-объекты
    return obj if isinstance(obj, InlineKeyboardMarkup) else None


def reply_for_edit(codec, reply):
    obj = serializer.decode_reply(codec, reply)
    return obj if isinstance(obj, InlineKeyboardMarkup) else None


def actual_id(scope, fallback, result):
    if scope.inline_id:
        return fallback
    mid = getattr(result, "message_id", None)
    return mid if mid is not None else fallback


def log_edit_fail(scope, payload, note):
    jlog(logger, logging.WARNING, LogCode.GATEWAY_EDIT_FAIL, scope=scope_kv(scope), payload=payload_kind(payload),
         note=note)


def log_edit_ok(scope, payload, mid):
    jlog(logger, logging.INFO, LogCode.GATEWAY_EDIT_OK, scope=scope_kv(scope), payload=payload_kind(payload),
         message={"id": mid, "extra_len": 0})


def finalize(scope, payload, id, result):
    mid = actual_id(scope, id, result)
    meta = extract_meta(result, payload, scope)
    log_edit_ok(scope, payload, mid)
    return Result(id=mid, extra=[], **meta)

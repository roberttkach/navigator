import logging

from aiogram.types import InlineKeyboardMarkup

from .util import extract
from .. import serializer
from ....domain.log.emit import jlog
from ....domain.port.message import Result
from ....domain.service.rendering.helpers import classify
from ....domain.service.scope import profile
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


def markup(codec, reply, *, edit: bool):
    obj = serializer.decode(codec, reply)
    if not edit:
        return obj
    return obj if isinstance(obj, InlineKeyboardMarkup) else None


def finalize(scope, payload, identifier, result):
    if scope.inline:
        marker = identifier
    else:
        fallback = getattr(result, "message_id", None)
        marker = fallback if fallback is not None else identifier
    meta = extract(result, payload, scope)
    jlog(
        logger,
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": marker, "extra_len": 0},
    )
    return Result(id=marker, extra=[], **meta)

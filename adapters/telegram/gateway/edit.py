import logging
from typing import Any, Dict

from .common import markup, finalize
from .retry import invoke
from .util import targets as _targets
from .. import media as media_mapper
from .. import serializer
from ..keyfilter import screen
from ....domain.constants import CaptionLimit, TextLimit
from ....domain.error import MessageEditForbidden, EmptyPayload, TextTooLong, CaptionTooLong
from ....domain.log.emit import jlog
from ....domain.port.markup import MarkupCodec
from ....domain.port.message import Result
from ....domain.service.rendering.helpers import classify as _classify
from ....domain.service.scope import profile
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


async def rewrite(bot, codec: MarkupCodec, scope: Scope, message: int, payload, *,
                  truncate: bool = False) -> Result:
    raw = "" if payload.text is None else str(payload.text)
    if not raw.strip():
        raise EmptyPayload()
    if len(raw) > TextLimit:
        if truncate:
            raw = raw[:TextLimit]
            jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="rewrite")
        else:
            raise TextTooLong()
    extras = serializer.scrub(scope, payload.extra, editing=True)
    cleaned = serializer.cleanse(
        extras, captioning=False, target=bot.edit_message_text, length=len(raw)
    )
    target = _targets(scope, message)
    try:
        result = await invoke(
            bot.edit_message_text,
            text=raw,
            reply_markup=markup(codec, payload.reply, edit=True),
            link_preview_options=serializer.preview(payload.preview),
            **target,
            **cleaned,
        )
    except Exception as e:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note=type(e).__name__,
        )
        raise
    return finalize(scope, payload, message, result)


async def recast(bot, codec: MarkupCodec, scope: Scope, message: int, payload, *,
                 truncate: bool = False) -> Result:
    if not payload.media:
        raise ValueError("Cannot edit media without a media payload")
    extras = serializer.scrub(scope, payload.extra, editing=True)
    caption = serializer.caption(payload)
    local = not bool(scope.inline)
    try:
        medium = media_mapper.compose(
            payload.media, caption, extra=extras, allow_local=local, truncate=truncate
        )
    except MessageEditForbidden:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note="inline_upload_forbidden",
        )
        raise
    target = _targets(scope, message)
    try:
        result = await invoke(
            bot.edit_message_media,
            media=medium,
            reply_markup=markup(codec, payload.reply, edit=True),
            **target,
        )
    except Exception as e:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note=type(e).__name__,
        )
        raise
    return finalize(scope, payload, message, result)


async def retitle(bot, codec: MarkupCodec, scope: Scope, message: int, payload, *,
                  truncate: bool = False) -> Result:
    extras = serializer.scrub(scope, payload.extra, editing=True)
    bundle = serializer.divide(extras)
    caption = serializer.restate(payload)
    length = len(caption) if caption is not None else 0
    cleaned = serializer.cleanse(
        bundle["caption"], captioning=True, target=bot.edit_message_caption, length=length
    )
    target = _targets(scope, message)
    if caption is not None and len(caption) > CaptionLimit:
        if truncate:
            caption = caption[:CaptionLimit]
            jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="retitle")
        else:
            raise CaptionTooLong()
    try:
        arguments: Dict[str, Any] = {
            "reply_markup": markup(codec, payload.reply, edit=True),
            **target,
            **cleaned,
        }
        if caption is not None:
            arguments["caption"] = caption
        settings: Dict[str, Any] = {}
        if (bundle["media"] or {}).get("show_caption_above_media") is not None:
            settings["show_caption_above_media"] = bool((bundle["media"] or {}).get("show_caption_above_media"))
        initial = dict(settings)
        screened = screen(bot.edit_message_caption, settings)
        if set(initial.keys()) != set(screened.keys()):
            jlog(
                logger,
                logging.DEBUG,
                LogCode.EXTRA_FILTERED_OUT,
                scope=profile(scope),
                stage="edit.caption.media",
                before=sorted(initial.keys()),
                after=sorted(screened.keys()),
                filtered_keys=sorted(set(initial) - set(screened)),
            )
        arguments.update(screened)
        result = await invoke(bot.edit_message_caption, **arguments)
    except Exception as e:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note=type(e).__name__,
        )
        raise
    return finalize(scope, payload, message, result)


async def remap(bot, codec: MarkupCodec, scope: Scope, message: int, payload) -> Result:
    target = _targets(scope, message)
    try:
        result = await invoke(
            bot.edit_message_reply_markup,
            reply_markup=markup(codec, payload.reply, edit=True),
            **target,
        )
    except Exception as e:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note=type(e).__name__,
        )
        raise
    return finalize(scope, payload, message, result)

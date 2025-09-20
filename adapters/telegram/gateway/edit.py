import logging
from typing import Any, Dict

from .common import reply_for_edit, log_edit_fail, finalize
from .retry import call_tg
from .util import targets as _targets
from .. import media as media_mapper
from .. import serializer
from ..keyfilter import accept_for
from ....domain.constants import TEXT_MAX, CAPTION_MAX
from ....domain.error import MessageEditForbidden, EmptyPayload, TextTooLong, CaptionTooLong
from ....domain.log.emit import jlog
from ....domain.port.markup import MarkupCodec
from ....domain.port.message import Result
from ....domain.service.rendering.helpers import payload_kind as _payload_kind
from ....domain.service.scope import scope_kv
from ....domain.value.message import Scope
from ....logging.code import LogCode

logger = logging.getLogger(__name__)


async def do_edit_text(bot, codec: MarkupCodec, scope: Scope, message_id: int, payload, *,
                       truncate: bool = False) -> Result:
    raw = "" if payload.text is None else str(payload.text)
    if not raw.strip():
        raise EmptyPayload()
    if len(raw) > TEXT_MAX:
        if truncate:
            raw = raw[:TEXT_MAX]
            jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=scope_kv(scope), stage="edit.text")
        else:
            raise TextTooLong()
    norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=True)
    kwargs = serializer.sanitize_text_kwargs(
        norm_extra, is_caption=False, target=bot.edit_message_text, text_len=len(raw)
    )
    trg = _targets(scope, message_id)
    try:
        result = await call_tg(
            bot.edit_message_text,
            text=raw,
            reply_markup=reply_for_edit(codec, payload.reply),
            link_preview_options=serializer.map_preview(payload.preview),
            **trg,
            **kwargs,
        )
    except Exception as e:
        log_edit_fail(scope, payload, type(e).__name__)
        raise
    return finalize(scope, payload, message_id, result)


async def do_edit_media(bot, codec: MarkupCodec, scope: Scope, message_id: int, payload, *,
                        truncate: bool = False) -> Result:
    if not payload.media:
        raise ValueError("Cannot edit media without a media payload")
    norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=True)
    caption = serializer.caption_for(payload)
    allow_local = not bool(scope.inline_id)
    try:
        tg_media = media_mapper.to_input_media(
            payload.media, caption, extra=norm_extra, allow_local=allow_local, truncate=truncate
        )
    except MessageEditForbidden:
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_EDIT_FAIL,
            scope=scope_kv(scope),
            payload=_payload_kind(payload),
            note="inline_upload_forbidden",
        )
        raise
    trg = _targets(scope, message_id)
    try:
        result = await call_tg(
            bot.edit_message_media,
            media=tg_media,
            reply_markup=reply_for_edit(codec, payload.reply),
            **trg,
        )
    except Exception as e:
        log_edit_fail(scope, payload, type(e).__name__)
        raise
    return finalize(scope, payload, message_id, result)


async def do_edit_caption(bot, codec: MarkupCodec, scope: Scope, message_id: int, payload, *,
                          truncate: bool = False) -> Result:
    norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=True)
    cap_extra, media_extra = serializer.split_extra(norm_extra)
    caption = serializer.caption_for_edit(payload)
    cap_len = len(caption) if caption is not None else 0
    kwargs = serializer.sanitize_text_kwargs(
        cap_extra, is_caption=True, target=bot.edit_message_caption, text_len=cap_len
    )
    trg = _targets(scope, message_id)
    # caption=None — не изменяем подпись; caption="" — очищаем подпись (см. serializer.caption_for_edit).
    if caption is not None and len(caption) > CAPTION_MAX:
        if truncate:
            caption = caption[:CAPTION_MAX]
            jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=scope_kv(scope), stage="edit.caption")
        else:
            raise CaptionTooLong()
    try:
        call_kwargs: Dict[str, Any] = {
            "reply_markup": reply_for_edit(codec, payload.reply),
            **trg,
            **kwargs,
        }
        if caption is not None:
            call_kwargs["caption"] = caption
        media_kwargs: Dict[str, Any] = {}
        if (media_extra or {}).get("show_caption_above_media") is not None:
            media_kwargs["show_caption_above_media"] = bool((media_extra or {}).get("show_caption_above_media"))
        raw_media_kwargs = dict(media_kwargs)
        filtered_media_kwargs = accept_for(bot.edit_message_caption, media_kwargs)
        if set(raw_media_kwargs.keys()) != set(filtered_media_kwargs.keys()):
            jlog(
                logger,
                logging.DEBUG,
                LogCode.EXTRA_FILTERED_OUT,
                scope=scope_kv(scope),
                stage="edit.caption.media",
                before=sorted(raw_media_kwargs.keys()),
                after=sorted(filtered_media_kwargs.keys()),
                filtered_keys=sorted(set(raw_media_kwargs) - set(filtered_media_kwargs)),
            )
        call_kwargs.update(filtered_media_kwargs)
        result = await call_tg(bot.edit_message_caption, **call_kwargs)
    except Exception as e:
        log_edit_fail(scope, payload, type(e).__name__)
        raise
    return finalize(scope, payload, message_id, result)


async def do_edit_markup(bot, codec: MarkupCodec, scope: Scope, message_id: int, payload) -> Result:
    trg = _targets(scope, message_id)
    try:
        result = await call_tg(
            bot.edit_message_reply_markup,
            reply_markup=reply_for_edit(codec, payload.reply),
            **trg,
        )
    except Exception as e:
        log_edit_fail(scope, payload, type(e).__name__)
        raise
    return finalize(scope, payload, message_id, result)

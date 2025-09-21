import logging
from inspect import signature
from typing import Any, Dict

from .common import reply_for_send
from .retry import call_tg
from .util import extract_meta
from .util import targets as _targets
from .. import media as media_mapper
from .. import serializer
from ..keyfilter import accept_for
from ....domain.constants import CaptionLimit, TextLimit
from ....domain.error import EmptyPayload, MessageEditForbidden, TextTooLong, CaptionTooLong
from ....domain.log.emit import jlog
from ....domain.port.markup import MarkupCodec
from ....domain.port.message import Result
from ....domain.service.rendering.helpers import classify as _classify
from ....domain.service.scope import profile
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


async def do_send(bot, codec: MarkupCodec, scope: Scope, payload, *, truncate: bool = False) -> Result:
    context = _targets(scope)
    inline = bool(scope.inline)
    allow_local = not inline
    try:
        if payload.group:
            norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=False)
            tg_group = media_mapper.group_to_input(
                payload.group, extra=norm_extra, allow_local=allow_local, truncate=truncate
            )
            ctx = accept_for(bot.send_media_group, context)
            sent_messages = await call_tg(bot.send_media_group, media=tg_group, **ctx)
            items = []
            for m in sent_messages:
                if m.photo:
                    items.append({"media_type": "photo", "file_id": m.photo[-1].file_id, "caption": m.caption})
                elif m.video:
                    items.append({"media_type": "video", "file_id": m.video.file_id, "caption": m.caption})
                elif m.animation:
                    items.append({"media_type": "animation", "file_id": m.animation.file_id, "caption": m.caption})
                elif m.document:
                    items.append({"media_type": "document", "file_id": m.document.file_id, "caption": m.caption})
                elif m.audio:
                    items.append({"media_type": "audio", "file_id": m.audio.file_id, "caption": m.caption})
            jlog(
                logger,
                logging.INFO,
                LogCode.GATEWAY_SEND_OK,
                scope=profile(scope),
                payload=_classify(payload),
                message={"id": sent_messages[0].message_id, "extra_len": len(sent_messages) - 1},
            )
            meta = {"kind": "group", "group_items": items, "inline": scope.inline}
            return Result(
                id=sent_messages[0].message_id,
                extra=[m.message_id for m in sent_messages[1:]],
                **meta,
            )
        if payload.media:
            try:
                tg_media = media_mapper.to_input_file(payload.media, allow_local=allow_local)
            except MessageEditForbidden:
                jlog(
                    logger,
                    logging.WARNING,
                    LogCode.GATEWAY_SEND_FAIL,
                    scope=profile(scope),
                    payload=_classify(payload),
                    note="inline_upload_forbidden",
                )
                raise
            sender = getattr(bot, f"send_{payload.media.type.value}")
            caption = serializer.caption_for(payload)
            if caption is not None and len(caption) > CaptionLimit:
                if truncate:
                    caption = caption[:CaptionLimit]
                    jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="send.caption")
                else:
                    raise CaptionTooLong()
            norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=False)
            cap_extra, media_extra = serializer.split_extra(norm_extra)
            caption_len = len(caption) if caption is not None else 0
            caption_kwargs = serializer.sanitize_text_kwargs(
                cap_extra, is_caption=True, target=sender, text_len=caption_len
            )

            opts: Dict[str, Any] = media_extra or {}
            media_kwargs: Dict[str, Any] = {}
            t = payload.media.type.value
            if t in ("photo", "video", "animation"):
                if opts.get("spoiler") is not None:
                    media_kwargs["has_spoiler"] = bool(opts.get("spoiler"))
                if opts.get("show_caption_above_media") is not None:
                    media_kwargs["show_caption_above_media"] = bool(opts.get("show_caption_above_media"))
            if t == "video":
                if opts.get("start") is not None:
                    media_kwargs["start_timestamp"] = opts.get("start")
            if t in ("video", "animation", "audio", "document"):
                if opts.get("thumb") is not None:
                    media_kwargs["thumbnail"] = media_mapper.as_input_file(
                        opts.get("thumb"), allow_local=allow_local
                    )
            if t == "audio":
                if opts.get("title") is not None:
                    media_kwargs["title"] = opts.get("title")
                if opts.get("performer") is not None:
                    media_kwargs["performer"] = opts.get("performer")
                if opts.get("duration") is not None:
                    media_kwargs["duration"] = opts.get("duration")
            if t in ("video", "animation"):
                if opts.get("width") is not None:
                    media_kwargs["width"] = opts.get("width")
                if opts.get("height") is not None:
                    media_kwargs["height"] = opts.get("height")
                if opts.get("duration") is not None:
                    media_kwargs["duration"] = opts.get("duration")

            raw_media_kwargs = dict(media_kwargs)
            filtered_media_kwargs = accept_for(sender, media_kwargs)
            if set(raw_media_kwargs.keys()) != set(filtered_media_kwargs.keys()):
                jlog(
                    logger,
                    logging.DEBUG,
                    LogCode.EXTRA_FILTERED_OUT,
                    scope=profile(scope),
                    stage="send.media",
                    before=sorted(raw_media_kwargs.keys()),
                    after=sorted(filtered_media_kwargs.keys()),
                    filtered_keys=sorted(set(raw_media_kwargs) - set(filtered_media_kwargs)),
                )
            media_kwargs = filtered_media_kwargs
            call_kwargs: Dict[str, Any] = {
                **context,
                **{payload.media.type.value: tg_media},
                "reply_markup": reply_for_send(codec, payload.reply),
                **caption_kwargs,
                **media_kwargs,
            }
            if caption is not None and "caption" in signature(sender).parameters:
                call_kwargs["caption"] = caption
            sent_message = await call_tg(sender, **call_kwargs)
        else:
            raw = "" if payload.text is None else str(payload.text)
            if not raw.strip():
                raise EmptyPayload()
            if len(raw) > TextLimit:
                if truncate:
                    raw = raw[:TextLimit]
                    jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="send.text")
                else:
                    raise TextTooLong()
            norm_extra = serializer.normalize_extra_for(scope, payload.extra, is_edit=False)
            raw_len = len(raw)
            text_kwargs = serializer.sanitize_text_kwargs(
                norm_extra, is_caption=False, target=bot.send_message, text_len=raw_len
            )
            sent_message = await call_tg(
                bot.send_message,
                **context,
                text=raw,
                reply_markup=reply_for_send(codec, payload.reply),
                link_preview_options=serializer.map_preview(payload.preview),
                **text_kwargs,
            )
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(scope),
            payload=_classify(payload),
            message={"id": sent_message.message_id, "extra_len": 0},
        )
        meta = extract_meta(sent_message, payload, scope)
        return Result(id=sent_message.message_id, extra=[], **meta)
    except MessageEditForbidden:
        raise
    except Exception as e:
        note = getattr(e, "message", None) or str(e)
        jlog(
            logger,
            logging.WARNING,
            LogCode.GATEWAY_SEND_FAIL,
            scope=profile(scope),
            payload=_classify(payload),
            note=str(note)[:300],
        )
        raise

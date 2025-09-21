import logging
from inspect import signature
from typing import Any, Dict

from .common import markup
from .retry import invoke
from .util import extract
from .util import targets as _targets
from .. import media as media_mapper
from .. import serializer
from ..keyfilter import screen
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


async def dispatch(bot, codec: MarkupCodec, scope: Scope, payload, *, truncate: bool = False) -> Result:
    context = _targets(scope)
    inline = bool(scope.inline)
    local = not inline
    try:
        if payload.group:
            extras = serializer.scrub(scope, payload.extra, editing=False)
            bundle = media_mapper.assemble(
                payload.group, extra=extras, allow_local=local, truncate=truncate
            )
            filtered = screen(bot.send_media_group, context)
            messages = await invoke(bot.send_media_group, media=bundle, **filtered)
            items = []
            for message in messages:
                if message.photo:
                    items.append({"media_type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption})
                elif message.video:
                    items.append({"media_type": "video", "file_id": message.video.file_id, "caption": message.caption})
                elif message.animation:
                    items.append({"media_type": "animation", "file_id": message.animation.file_id, "caption": message.caption})
                elif message.document:
                    items.append({"media_type": "document", "file_id": message.document.file_id, "caption": message.caption})
                elif message.audio:
                    items.append({"media_type": "audio", "file_id": message.audio.file_id, "caption": message.caption})
            jlog(
                logger,
                logging.INFO,
                LogCode.GATEWAY_SEND_OK,
                scope=profile(scope),
                payload=_classify(payload),
                message={"id": messages[0].message_id, "extra_len": len(messages) - 1},
            )
            meta = {"kind": "group", "group_items": items, "inline": scope.inline}
            return Result(
                id=messages[0].message_id,
                extra=[message.message_id for message in messages[1:]],
                **meta,
            )
        if payload.media:
            try:
                medium = media_mapper.convert(payload.media, allow_local=local)
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
            caption = serializer.caption(payload)
            if caption is not None and len(caption) > CaptionLimit:
                if truncate:
                    caption = caption[:CaptionLimit]
                    jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="send.caption")
                else:
                    raise CaptionTooLong()
            extras = serializer.scrub(scope, payload.extra, editing=False)
            bundle = serializer.divide(extras)
            length = len(caption) if caption is not None else 0
            options: Dict[str, Any] = bundle["media"] or {}
            settings: Dict[str, Any] = {}
            kind = payload.media.type.value
            if kind in ("photo", "video", "animation"):
                if options.get("spoiler") is not None:
                    settings["has_spoiler"] = bool(options.get("spoiler"))
                if options.get("show_caption_above_media") is not None:
                    settings["show_caption_above_media"] = bool(options.get("show_caption_above_media"))
            if kind == "video":
                if options.get("start") is not None:
                    settings["start_timestamp"] = options.get("start")
            if kind in ("video", "animation", "audio", "document"):
                if options.get("thumb") is not None:
                    settings["thumbnail"] = media_mapper.adapt(
                        options.get("thumb"), allow_local=local
                    )
            if kind == "audio":
                if options.get("title") is not None:
                    settings["title"] = options.get("title")
                if options.get("performer") is not None:
                    settings["performer"] = options.get("performer")
                if options.get("duration") is not None:
                    settings["duration"] = options.get("duration")
            if kind in ("video", "animation"):
                if options.get("width") is not None:
                    settings["width"] = options.get("width")
                if options.get("height") is not None:
                    settings["height"] = options.get("height")
                if options.get("duration") is not None:
                    settings["duration"] = options.get("duration")

            initial = dict(settings)
            screened = screen(sender, settings)
            if set(initial.keys()) != set(screened.keys()):
                jlog(
                    logger,
                    logging.DEBUG,
                    LogCode.EXTRA_FILTERED_OUT,
                    scope=profile(scope),
                    stage="send.media",
                    before=sorted(initial.keys()),
                    after=sorted(screened.keys()),
                    filtered_keys=sorted(set(initial) - set(screened)),
                )
            settings = screened
            arguments: Dict[str, Any] = {
                **context,
                **{payload.media.type.value: medium},
                "reply_markup": markup(codec, payload.reply, edit=False),
                **serializer.cleanse(
                    bundle["caption"],
                    captioning=True,
                    target=sender,
                    length=length,
                ),
                **settings,
            }
            if caption is not None and "caption" in signature(sender).parameters:
                arguments["caption"] = caption
            message = await invoke(sender, **arguments)
        else:
            text = "" if payload.text is None else str(payload.text)
            if not text.strip():
                raise EmptyPayload()
            if len(text) > TextLimit:
                if truncate:
                    text = text[:TextLimit]
                    jlog(logger, logging.INFO, LogCode.TOO_LONG_TRUNCATED, scope=profile(scope), stage="send.text")
                else:
                    raise TextTooLong()
            extras = serializer.scrub(scope, payload.extra, editing=False)
            message = await invoke(
                bot.send_message,
                **context,
                text=text,
                reply_markup=markup(codec, payload.reply, edit=False),
                link_preview_options=serializer.preview(payload.preview),
                **serializer.cleanse(
                    extras,
                    captioning=False,
                    target=bot.send_message,
                    length=len(text),
                ),
            )
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(scope),
            payload=_classify(payload),
            message={"id": message.message_id, "extra_len": 0},
        )
        meta = extract(message, payload, scope)
        return Result(id=message.message_id, extra=[], **meta)
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

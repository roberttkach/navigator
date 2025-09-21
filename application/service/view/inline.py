import json
import logging
import re

from ..store import preserve
from ...internal.rules.inline import remap as _inline_remap
from ....domain.entity.history import Entry
from ....domain.entity.media import MediaType
from ....domain.log.emit import jlog
from ....domain.service.rendering import decision as _d
from ....domain.service.rendering.config import RenderingConfig
from ....domain.util.path import local, remote
from ....domain.log.code import LogCode


def _canon(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":")) if isinstance(d, dict) else None


_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-=]{20,}$")


def _looks_like_file_id(s: str) -> bool:
    return bool(_FILE_ID_RE.match(s))


class InlineStrategy:
    def __init__(self, gateway, is_url_input_file, strict_inline_media_path):
        self._gateway = gateway
        self._is_url_input_file = is_url_input_file
        self._logger = logging.getLogger(__name__)
        self._strict_inline_media_path = strict_inline_media_path

    def _media_editable_inline(self, p) -> bool:
        """
        Inline-редакции медиа разрешены только если дескриптор пути:
        - URLInputFile;
        - валидный http(s) URL;
        - строка, не являющаяся локальным путём и похожая на Telegram file_id (при STRICT=1).
        Локальные пути запрещены.
        """
        m = getattr(p, "media", None)
        if not m:
            return False
        if getattr(m, "type", None) in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            return False
        path = getattr(m, "path", None)
        if self._is_url_input_file(path):
            return True
        if isinstance(path, str):
            if remote(path):
                return True
            if not local(path):
                return _looks_like_file_id(path) if self._strict_inline_media_path else True
        return False

    def _reply_changed(self, base_msg, p) -> bool:
        """True, если отличается только клавиатура (Markup.kind/data)."""
        ra = getattr(base_msg, "markup", None)
        rb = getattr(p, "reply", None)
        if (ra is None) and (rb is None):
            return False
        if (ra is None) != (rb is None):
            return True
        try:
            same_kind = getattr(ra, "kind", None) == getattr(rb, "kind", None)
            same_data = _canon(getattr(ra, "data", None)) == _canon(getattr(rb, "data", None))
            return not (same_kind and same_data)
        except Exception:
            return True

    async def handle_element(
            self,
            *,
            scope,
            payload,
            last_message,
            inline,
            swap,
            rendering_config: RenderingConfig,
    ):
        if inline:
            p = preserve(payload, last_message)
            if getattr(p, "group", None):
                p = p.morph(media=p.group[0], group=None)

            base_msg = last_message
            m = getattr(p, "media", None)

            if m:
                if getattr(m, "type", None) in (MediaType.VOICE,
                                                MediaType.VIDEO_NOTE) or not self._media_editable_inline(p):
                    if base_msg and self._reply_changed(base_msg, p):
                        return await swap(
                            scope,
                            p.morph(media=base_msg.media if base_msg else None, group=None),
                            last_message,
                            _d.Decision.EDIT_MARKUP,
                        )
                    jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                    return None
                base = Entry(state=None, view=None, messages=[last_message]) if last_message else None
                dec0 = _d.decide(base, p, rendering_config)
                if dec0 is _d.Decision.DELETE_SEND:
                    dec1 = _inline_remap(base_msg, p, inline=True)
                    jlog(self._logger, logging.INFO, LogCode.INLINE_REMAP_DELETE_SEND, from_="DELETE_SEND",
                         to_=dec1.name)
                    if dec1 is _d.Decision.EDIT_MARKUP:
                        return await swap(
                            scope,
                            p.morph(media=base_msg.media, group=None),
                            last_message,
                            _d.Decision.EDIT_MARKUP,
                        )
                    if dec1 is _d.Decision.EDIT_TEXT:
                        return await swap(scope, p, last_message, _d.Decision.EDIT_TEXT)
                    if dec1 is _d.Decision.EDIT_MEDIA:
                        return await swap(scope, p, last_message, _d.Decision.EDIT_MEDIA)
                    jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                    return None
                if dec0 is _d.Decision.EDIT_MEDIA_CAPTION:
                    return await swap(scope, p, last_message, _d.Decision.EDIT_MEDIA_CAPTION)
                if dec0 is _d.Decision.EDIT_MARKUP:
                    return await swap(scope, p, last_message, _d.Decision.EDIT_MARKUP)
                return await swap(scope, p, last_message, _d.Decision.EDIT_MEDIA)

            if base_msg and getattr(base_msg, "media", None):
                has_caption_change = (
                        p.text is not None
                        or ((p.extra or {}).get("mode") is not None)
                        or ((p.extra or {}).get("entities") is not None)
                        or ((p.extra or {}).get("show_caption_above_media") is not None)
                )
                if has_caption_change:
                    return await swap(
                        scope,
                        p.morph(media=base_msg.media, group=None),
                        last_message,
                        _d.Decision.EDIT_MEDIA_CAPTION,
                    )
                if self._reply_changed(base_msg, p):
                    return await swap(
                        scope,
                        p.morph(media=base_msg.media, group=None),
                        last_message,
                        _d.Decision.EDIT_MARKUP,
                    )
                jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                return None

            # Обычный текст→текст.
            return await swap(scope, p, last_message, _d.Decision.EDIT_TEXT)

        rr = await swap(scope, payload, None, _d.Decision.RESEND)
        return rr

import json
import logging
import re

from ..store import preserve
from ...internal.rules.inline import remap as _inline
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

class InlineStrategy:
    def __init__(self, gateway, probe, strictpath):
        self._gateway = gateway
        self._probe = probe
        self._logger = logging.getLogger(__name__)
        self._strictpath = strictpath

    def _inlineable(self, payload) -> bool:
        """
        Inline-редакции медиа разрешены только если дескриптор пути:
        - URLInputFile;
        - валидный http(s) URL;
        - строка, не являющаяся локальным путём и похожая на Telegram file_id (при STRICT=1).
        Локальные пути запрещены.
        """
        m = getattr(payload, "media", None)
        if not m:
            return False
        if getattr(m, "type", None) in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            return False
        path = getattr(m, "path", None)
        if self._probe(path):
            return True
        if isinstance(path, str):
            if remote(path):
                return True
            if not local(path):
                return bool(_FILE_ID_RE.match(path)) if self._strictpath else True
        return False

    def _replydelta(self, base, payload) -> bool:
        """True, если отличается только клавиатура (Markup.kind/data)."""
        ra = getattr(base, "markup", None)
        rb = getattr(payload, "reply", None)
        if (ra is None) and (rb is None):
            return False
        if (ra is None) != (rb is None):
            return True
        try:
            return not (
                getattr(ra, "kind", None) == getattr(rb, "kind", None)
                and _canon(getattr(ra, "data", None)) == _canon(getattr(rb, "data", None))
            )
        except Exception:
            return True

    async def handle(
            self,
            *,
            scope,
            payload,
            tail,
            swap,
            config: RenderingConfig,
    ):
        entry = preserve(payload, tail)
        if getattr(entry, "group", None):
            entry = entry.morph(media=entry.group[0], group=None)

        base = tail
        media = getattr(entry, "media", None)

        if media:
            if getattr(media, "type", None) in (
                    MediaType.VOICE,
                    MediaType.VIDEO_NOTE,
            ) or not self._inlineable(entry):
                if base and self._replydelta(base, entry):
                    return await swap(
                        scope,
                        entry.morph(media=base.media if base else None, group=None),
                        tail,
                        _d.Decision.EDIT_MARKUP,
                    )
                jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                return None
            anchor = Entry(state=None, view=None, messages=[tail]) if tail else None
            verdict = _d.decide(anchor, entry, config)
            if verdict is _d.Decision.DELETE_SEND:
                remap = _inline(base, entry, inline=True)
                jlog(self._logger, logging.INFO, LogCode.INLINE_REMAP_DELETE_SEND, origin="DELETE_SEND",
                     target=remap.name)
                if remap is _d.Decision.EDIT_MARKUP:
                    return await swap(
                        scope,
                        entry.morph(media=base.media, group=None),
                        tail,
                        _d.Decision.EDIT_MARKUP,
                    )
                if remap is _d.Decision.EDIT_TEXT:
                    return await swap(scope, entry, tail, _d.Decision.EDIT_TEXT)
                if remap is _d.Decision.EDIT_MEDIA:
                    return await swap(scope, entry, tail, _d.Decision.EDIT_MEDIA)
                jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                return None
            if verdict is _d.Decision.EDIT_MEDIA_CAPTION:
                return await swap(scope, entry, tail, _d.Decision.EDIT_MEDIA_CAPTION)
            if verdict is _d.Decision.EDIT_MARKUP:
                return await swap(scope, entry, tail, _d.Decision.EDIT_MARKUP)
            return await swap(scope, entry, tail, _d.Decision.EDIT_MEDIA)

        if base and getattr(base, "media", None):
            captiondelta = (
                    entry.text is not None
                    or ((entry.extra or {}).get("mode") is not None)
                    or ((entry.extra or {}).get("entities") is not None)
                    or ((entry.extra or {}).get("show_caption_above_media") is not None)
            )
            if captiondelta:
                return await swap(
                    scope,
                    entry.morph(media=base.media, group=None),
                    tail,
                    _d.Decision.EDIT_MEDIA_CAPTION,
                )
            if self._replydelta(base, entry):
                return await swap(
                    scope,
                    entry.morph(media=base.media, group=None),
                    tail,
                    _d.Decision.EDIT_MARKUP,
                )
            jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
            return None

        return await swap(scope, entry, tail, _d.Decision.EDIT_TEXT)

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Any

from .helpers import match as _match_markups
from ...entity.history import Entry
from ...entity.media import MediaType
from ...value.content import Payload, caption
from .config import RenderingConfig


class Decision(Enum):
    RESEND = auto()
    EDIT_TEXT = auto()
    EDIT_MEDIA_CAPTION = auto()
    EDIT_MEDIA = auto()
    EDIT_MARKUP = auto()
    DELETE_SEND = auto()
    NO_CHANGE = auto()


def _has_group(x) -> bool:
    if x is None:
        return False
    mg = getattr(x, "group", None)
    return bool(mg)


def _has_media_single(x) -> bool:
    if x is None:
        return False
    return bool(getattr(x, "media", None))


def _has_any_media(x) -> bool:
    return _has_group(x) or _has_media_single(x)


@dataclass(frozen=True, slots=True)
class _MediaCaptionOpts:
    show_caption_above_media: bool


@dataclass(frozen=True, slots=True)
class _MediaEditOpts:
    spoiler: bool
    start: object
    thumb_present: bool


def _view_of(obj: Any):
    """Normalize to an object with attributes: text, media, group, reply, extra."""
    if obj is None:
        return type("V", (), dict(text=None, media=None, group=None, reply=None, extra=None))()
    if isinstance(obj, Entry):
        m = obj.messages[0] if (getattr(obj, "messages", None) or []) else None
        return type("V", (), dict(
            text=getattr(m, "text", None),
            media=getattr(m, "media", None),
            group=getattr(m, "group", None),
            reply=getattr(m, "markup", None),
            extra=getattr(m, "extra", None),
        ))()
    return obj


def _norm_text_caption_extra(obj) -> dict:
    """
    Нормализация extra для текста/подписи:
    учитываются только mode/entities. message_effect_id игнорируется.
    """
    v = getattr(_view_of(obj), "extra", None) or {}
    out = {}
    if "mode" in v:
        out["mode"] = v["mode"]
    if "entities" in v:
        out["entities"] = v["entities"]
    return out


def _text_extra_equal(a, b) -> bool:
    return _norm_text_caption_extra(a) == _norm_text_caption_extra(b)


def _caption_extra_equal(a, b) -> bool:
    return _norm_text_caption_extra(a) == _norm_text_caption_extra(b)


def _media_opts_split(e, config: RenderingConfig) -> tuple[_MediaCaptionOpts, _MediaEditOpts]:
    """
    Делит медиа-опции на:
      - влияющие на подпись/её позицию (EDIT_MEDIA_CAPTION),
      - требующие полной замены медиа (EDIT_MEDIA).
    """
    x = getattr(_view_of(e), "extra", {}) or {}
    cap = _MediaCaptionOpts(show_caption_above_media=bool(x.get("show_caption_above_media")))
    st = x.get("start")
    try:
        st = int(st) if st is not None else None
    except Exception:
        pass
    present = bool((x.get("thumb") is not None) or x.get("has_thumb"))
    edt = _MediaEditOpts(
        spoiler=bool(x.get("spoiler")),
        start=st,
        thumb_present=(present if config.thumbguard else False),
    )
    return cap, edt


def _text_of(obj) -> Optional[str]:
    if obj is None or _has_any_media(obj):
        return None
    t = getattr(obj, "text", None)
    return str(t).strip() if t is not None else None


def _reply_of(obj):
    if obj is None:
        return None
    if isinstance(obj, Entry):
        try:
            return getattr(obj.messages[0], "markup", None)
        except (IndexError, AttributeError, TypeError):
            return None
    return getattr(obj, "reply", None)


def _match(a, b) -> bool:
    ra = _reply_of(a)
    rb = _reply_of(b)
    return _match_markups(ra, rb)


def _preview_of(obj):
    if obj is None:
        return None
    if isinstance(obj, Entry):
        try:
            m = obj.messages[0] if obj.messages else None
            return getattr(m, "preview", None)
        except Exception:
            return None
    return getattr(obj, "preview", None)


def _preview_equal(a, b) -> bool:
    pa = _preview_of(a)
    pb = _preview_of(b)
    if pa is None and pb is None:
        return True
    if (pa is None) != (pb is None):
        return False
    return (
            getattr(pa, "url", None) == getattr(pb, "url", None)
            and bool(getattr(pa, "small", False)) == bool(getattr(pb, "small", False))
            and bool(getattr(pa, "large", False)) == bool(getattr(pb, "large", False))
            and bool(getattr(pa, "above", False)) == bool(getattr(pb, "above", False))
            and getattr(pa, "disabled", None) == getattr(pb, "disabled", None)
    )


def _same_media_file(o, n) -> bool:
    """
    Сравнение по Telegram file_id:
    - в истории o.media.path — это file_id (str),
    - «тот же файл» только если new.media.path — тоже str и равен старому file_id.
    """
    if not (o and getattr(o, "media", None) and n and getattr(n, "media", None)):
        return False
    if o.media.type != n.media.type:
        return False
    old_id = getattr(o.media, "path", None)
    new_path = getattr(n.media, "path", None)
    return isinstance(old_id, str) and isinstance(new_path, str) and (old_id == new_path)


def decide(old: Optional[object], new: Payload, config: RenderingConfig) -> Decision:
    """
    Контракт:
    - Любые группы в old/new ⇒ DELETE_SEND.
    - Частичное редактирование альбомов выполняется вне decide: ранняя ветка в
      ViewOrchestrator.render_node обрабатывает совместимые альбомы.
    - Inline-ограничения и ремап DELETE_SEND применяются на уровне стратегий inline.
    """
    if not old:
        return Decision.RESEND

    o = _view_of(old)
    n = _view_of(new)

    # Любые группы в old/new → DELETE_SEND
    if _has_group(o) or _has_group(n):
        return Decision.DELETE_SEND

    # Запрет VOICE/VIDEO_NOTE в редактировании: всегда DELETE_SEND
    if n.media and n.media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
        return Decision.DELETE_SEND
    if o.media and o.media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
        return Decision.DELETE_SEND

    # Переход media↔text → DELETE_SEND
    if _has_any_media(o) != _has_any_media(n):
        return Decision.DELETE_SEND

    # Текст↔текст
    if not _has_any_media(o) and not _has_any_media(n):
        if (_text_of(o) or "") == (_text_of(n) or ""):
            if (not _text_extra_equal(o, n)) or (not _preview_equal(o, n)):
                return Decision.EDIT_TEXT
            return Decision.NO_CHANGE if _match(o, n) else Decision.EDIT_MARKUP
        return Decision.EDIT_TEXT

    # Медиа↔медиа
    if _has_any_media(o) and _has_any_media(n):
        # Сравниваем только по file_id и типу
        if _same_media_file(o, n):
            cap_o, edt_o = _media_opts_split(o, config)
            cap_n, edt_n = _media_opts_split(n, config)

            # Любое изменение медиа-уровня (spoiler/start/thumb*) требует EDIT_MEDIA.
            if edt_o != edt_n:
                return Decision.EDIT_MEDIA

            same_caption_text = (caption(o) or "") == (caption(n) or "")
            same_caption_extra = _caption_extra_equal(o, n)
            same_caption_pos = (cap_o == cap_n)
            if same_caption_text and same_caption_extra and same_caption_pos:
                return Decision.NO_CHANGE if _match(o, n) else Decision.EDIT_MARKUP
            return Decision.EDIT_MEDIA_CAPTION
        return Decision.EDIT_MEDIA

    return Decision.NO_CHANGE

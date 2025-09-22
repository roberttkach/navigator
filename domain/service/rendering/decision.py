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


def _grouped(obj) -> bool:
    if obj is None:
        return False
    pack = getattr(obj, "group", None)
    return bool(pack)


def _single(obj) -> bool:
    if obj is None:
        return False
    return bool(getattr(obj, "media", None))


def _mediated(obj) -> bool:
    return _grouped(obj) or _single(obj)


@dataclass(frozen=True, slots=True)
class _CaptionFlag:
    above: bool


@dataclass(frozen=True, slots=True)
class _MediaFlag:
    spoiler: bool
    start: object
    thumb: bool


@dataclass(frozen=True, slots=True)
class _MediaProfile:
    caption: _CaptionFlag
    edit: _MediaFlag


def _view(obj: Any):
    """Normalize to an object with attributes: text, media, group, reply, extra."""
    if obj is None:
        return type("V", (), dict(text=None, media=None, group=None, reply=None, extra=None))()
    if isinstance(obj, Entry):
        message = obj.messages[0] if (getattr(obj, "messages", None) or []) else None
        return type(
            "V",
            (),
            dict(
                text=getattr(message, "text", None),
                media=getattr(message, "media", None),
                group=getattr(message, "group", None),
                reply=getattr(message, "markup", None),
                extra=getattr(message, "extra", None),
            ),
        )()
    return obj


def _extras(obj) -> dict:
    """
    Нормализация extra для текста/подписи:
    учитываются только mode/entities. message_effect_id игнорируется.
    """
    value = getattr(_view(obj), "extra", None) or {}
    out = {}
    if "mode" in value:
        out["mode"] = value["mode"]
    if "entities" in value:
        out["entities"] = value["entities"]
    return out


def _mediaplan(entry, config: RenderingConfig) -> _MediaProfile:
    payload = getattr(_view(entry), "extra", {}) or {}
    caption = _CaptionFlag(above=bool(payload.get("show_caption_above_media")))
    start = payload.get("start")
    try:
        start = int(start) if start is not None else None
    except Exception:
        pass
    present = bool((payload.get("thumb") is not None) or payload.get("has_thumb"))
    edit = _MediaFlag(
        spoiler=bool(payload.get("spoiler")),
        start=start,
        thumb=(present if config.thumbguard else False),
    )
    return _MediaProfile(caption=caption, edit=edit)


def _text(obj) -> Optional[str]:
    if obj is None or _mediated(obj):
        return None
    value = getattr(obj, "text", None)
    return str(value).strip() if value is not None else None


def _reply(obj):
    if obj is None:
        return None
    if isinstance(obj, Entry):
        try:
            return getattr(obj.messages[0], "markup", None)
        except (IndexError, AttributeError, TypeError):
            return None
    return getattr(obj, "reply", None)


def _replymatch(a, b) -> bool:
    return _match_markups(_reply(a), _reply(b))


def _preview(obj):
    if obj is None:
        return None
    if isinstance(obj, Entry):
        try:
            message = obj.messages[0] if obj.messages else None
            return getattr(message, "preview", None)
        except Exception:
            return None
    return getattr(obj, "preview", None)


def _previewmatch(a, b) -> bool:
    pa = _preview(a)
    pb = _preview(b)
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


def _samefile(old, new) -> bool:
    """
    Сравнение по Telegram file_id:
    - в истории o.media.path — это file_id (str),
    - «тот же файл» только если new.media.path — тоже str и равен старому file_id.
    """
    if not (old and getattr(old, "media", None) and new and getattr(new, "media", None)):
        return False
    if old.media.type != new.media.type:
        return False
    former = getattr(old.media, "path", None)
    latter = getattr(new.media, "path", None)
    return isinstance(former, str) and isinstance(latter, str) and (former == latter)


def decide(old: Optional[object], new: Payload, config: RenderingConfig) -> Decision:
    """
    Контракт:
    - Любые группы в old/new ⇒ DELETE_SEND.
    - Частичное редактирование альбомов выполняется вне decide: ранняя ветка в
      ViewOrchestrator.render обрабатывает совместимые альбомы.
    - Inline-ограничения и ремап DELETE_SEND применяются на уровне стратегий inline.
    """
    if not old:
        return Decision.RESEND

    prior = _view(old)
    fresh = _view(new)

    # Любые группы в old/new → DELETE_SEND
    if _grouped(prior) or _grouped(fresh):
        return Decision.DELETE_SEND

    # Запрет VOICE/VIDEO_NOTE в редактировании: всегда DELETE_SEND
    if fresh.media and fresh.media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
        return Decision.DELETE_SEND
    if prior.media and prior.media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
        return Decision.DELETE_SEND

    # Переход media↔text → DELETE_SEND
    if _mediated(prior) != _mediated(fresh):
        return Decision.DELETE_SEND

    # Текст↔текст
    if not _mediated(prior) and not _mediated(fresh):
        if (_text(prior) or "") == (_text(fresh) or ""):
            if (_extras(prior) != _extras(fresh)) or (not _previewmatch(prior, fresh)):
                return Decision.EDIT_TEXT
            return Decision.NO_CHANGE if _replymatch(prior, fresh) else Decision.EDIT_MARKUP
        return Decision.EDIT_TEXT

    # Медиа↔медиа
    if _mediated(prior) and _mediated(fresh):
        # Сравниваем только по file_id и типу
        if _samefile(prior, fresh):
            before = _mediaplan(prior, config)
            after = _mediaplan(fresh, config)

            # Любое изменение медиа-уровня (spoiler/start/thumb*) требует EDIT_MEDIA.
            if before.edit != after.edit:
                return Decision.EDIT_MEDIA

            if (
                (caption(prior) or "") == (caption(fresh) or "")
                and _extras(prior) == _extras(fresh)
                and before.caption == after.caption
            ):
                return Decision.NO_CHANGE if _replymatch(prior, fresh) else Decision.EDIT_MARKUP
            return Decision.EDIT_MEDIA_CAPTION
        return Decision.EDIT_MEDIA

    return Decision.NO_CHANGE

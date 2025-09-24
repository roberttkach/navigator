from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from .helpers import match
from ...entity.media import MediaType
from ...port.mediaid import MediaIdentityPolicy
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


class _BlankView:
    text = None
    media = None
    group = None
    reply = None
    extra = None


_BLANK_VIEW = _BlankView()


def _view(obj: Any):
    """Normalize to an object with attributes: text, media, group, reply, extra."""
    if obj is None:
        return _BLANK_VIEW
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


def _sketch(entry, config: RenderingConfig) -> _MediaProfile:
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
    return getattr(obj, "reply", getattr(obj, "markup", None))


def _preview(obj):
    if obj is None:
        return None
    return getattr(obj, "preview", None)


def _identical(old, new, policy: MediaIdentityPolicy) -> bool:
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
    return policy.same(former, latter, type=getattr(old.media.type, "value", ""))


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
            if (_extras(prior) != _extras(fresh)) or (_preview(prior) != _preview(fresh)):
                return Decision.EDIT_TEXT
            aligned = match(_reply(prior), _reply(fresh))
            return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP
        return Decision.EDIT_TEXT

    # Медиа↔медиа
    if _mediated(prior) and _mediated(fresh):
        # Сравниваем только по file_id и типу
        if _identical(prior, fresh, config.identity):
            before = _sketch(prior, config)
            after = _sketch(fresh, config)

            # Любое изменение медиа-уровня (spoiler/start/thumb*) требует EDIT_MEDIA.
            if before.edit != after.edit:
                return Decision.EDIT_MEDIA

            if (
                (caption(prior) or "") == (caption(fresh) or "")
                and _extras(prior) == _extras(fresh)
                and before.caption == after.caption
            ):
                aligned = match(_reply(prior), _reply(fresh))
                return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP
            return Decision.EDIT_MEDIA_CAPTION
        return Decision.EDIT_MEDIA

    return Decision.NO_CHANGE

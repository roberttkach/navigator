from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any
import warnings

from ..entity.markup import Markup
from ..entity.media import MediaItem
from ..types import Extra

if TYPE_CHECKING:
    from ..entity.history import Entry


@dataclass(frozen=True, slots=True)
class Preview:
    url: str | None = None
    small: bool = False
    large: bool = False
    above: bool = False
    disabled: bool | None = None


@dataclass(frozen=True, slots=True)
class Payload:
    text: str | None = None
    media: MediaItem | None = None
    group: list[MediaItem] | None = None
    reply: Markup | None = None
    preview: Preview | None = None
    extra: Extra | None = None
    clear_caption: bool = False

    def morph(self, **kw: Any) -> Payload:
        return replace(self, **kw)

    def with_(self, **kw: Any) -> Payload:
        warnings.warn("Payload.with_ is deprecated; use Payload.morph", DeprecationWarning, stacklevel=2)
        return self.morph(**kw)


def normalize(payload: Payload) -> Payload:
    media = payload.media
    group = payload.group
    if group and len(group) == 1:
        media = group[0]
        group = None
    if media and group:
        raise ValueError("payload_has_both_media_and_group")
    text = None if group else payload.text
    return Payload(
        text=text,
        media=media,
        group=group,
        reply=payload.reply,
        preview=payload.preview,
        extra=payload.extra,
        clear_caption=payload.clear_caption and not bool(group),
    )


def caption(x: Payload | Entry | None) -> str | None:
    """
    Возвращает подпись к медиа с приоритетом источника:
    1) Если есть group — возвращает None.
    2) Если text является непустой строкой — возвращает text (приоритет над caption).
    3) Иначе, если caption медиа непустая — возвращает её.
    4) Иначе None.
    Лишние пробелы по краям отбрасываются.

    Инвариант: прямые вызовы с «сырым» Entry не предназначены для клиентского кода.
    Для сравнения старого и нового представления используйте нормализованный вид
    (см. decision._view_of) или передавайте Payload.
    """
    if x is None:
        return None
    if getattr(x, "group", None):
        return None
    m = getattr(x, "media", None)
    if not m:
        return None
    t = getattr(x, "text", None)
    if isinstance(t, str):
        s = t.strip()
        if s:
            return s
    c = getattr(m, "caption", None)
    if isinstance(c, str):
        s = str(c).strip()
        return s if s else None
    return None


def resolve_content(payload: Payload) -> Payload:
    warnings.warn("resolve_content is deprecated; use normalize", DeprecationWarning, stacklevel=2)
    return normalize(payload)


def caption_of(x: Payload | Entry | None) -> str | None:
    warnings.warn("caption_of is deprecated; use caption", DeprecationWarning, stacklevel=2)
    return caption(x)

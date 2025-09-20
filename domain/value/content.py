from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, List, Union, Any, TYPE_CHECKING

from ..entity.markup import Markup
from ..entity.media import MediaItem
from ..types import Extra

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class Preview:
    url: Optional[str] = None
    small: bool = False
    large: bool = False
    above: bool = False
    disabled: Optional[bool] = None


@dataclass(frozen=True, slots=True)
class Payload:
    text: Optional[str] = None
    media: Optional[MediaItem] = None
    group: Optional[List[MediaItem]] = None
    reply: Optional[Markup] = None
    preview: Optional[Preview] = None
    extra: Optional[Extra] = None

    def with_(self, **kw: Any) -> "Payload":
        return replace(self, **kw)


def resolve_content(payload: Payload) -> Payload:
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
    )


def caption_of(x: Union[Payload, "Entry", None]) -> Optional[str]:
    """
    Возвращает подпись к медиа с приоритетом источника:
    1) Если есть group — возвращает None.
    2) Если text является непустой строкой — возвращает text (приоритет над caption).
    3) Иначе, если caption медиа непустая — возвращает её.
    4) Иначе None.
    Лишние пробелы по краям отбрасываются.

    Инвариант: прямые вызовы с «сырым» Entry не предназначены для клиентского кода.
    Для сравнения старого и нового представления используйте нормализованный вид (см. decision._view_of)
    или передавайте Payload.
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

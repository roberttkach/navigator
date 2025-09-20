from dataclasses import dataclass
from typing import Optional, List

from ...domain.entity.markup import Markup
from ...domain.types import Extra
from ...domain.value.content import Preview


@dataclass(frozen=True, slots=True)
class Media:
    path: object
    type: Optional[str] = None
    caption: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Content:
    """
    DTO контента для Navigator.

    Поле `extra`:
    - `message_effect_id` применяется только при отправке в приватных чатах.
    - При редактировании и/или вне приватных чатов эффект удаляется нормализацией.
    - Попытка изменить только эффект без изменения текста/медиа/markup логически приводит к NO_CHANGE.

    Очистка подписи:
    - Если media и clear_caption=True и text в значении None/"" →
      в payload.text будет установлен "" и установлен маркер явной очистки.
    - Если media и text == "" при clear_caption=False → выбрасывается ValueError.
    """
    text: Optional[str] = None
    media: Optional[Media] = None
    group: Optional[List[Media]] = None
    reply: Optional[Markup] = None
    preview: Optional[Preview] = None
    extra: Optional[Extra] = None
    clear_caption: bool = False


@dataclass(frozen=True, slots=True)
class Node:
    messages: List[Content]


__all__ = ["Content", "Media", "Node"]

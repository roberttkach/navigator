from __future__ import annotations

from typing import TypedDict, NotRequired, Literal, Any, Union


class Entity(TypedDict, total=False):
    type: Literal[
        "mention",
        "hashtag",
        "cashtag",
        "bot_command",
        "url",
        "email",
        "phone_number",
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "spoiler",
        "code",
        "pre",
        "text_link",
        "text_mention",
        "custom_emoji",
        "blockquote",
        "expandable_blockquote",
    ]
    offset: int
    length: int
    url: NotRequired[str]
    user: NotRequired[Any]
    language: NotRequired[str]
    custom_emoji_id: NotRequired[str]


class TextExtra(TypedDict, total=False):
    """
    Правила:
    - message_effect_id учитывается только при отправке в приватных чатах.
    - При edit и/или вне приватных чатов удаляется в процессе нормализации.
    """
    mode: Literal["HTML", "MarkdownV2"]
    entities: NotRequired[list[Entity]]
    message_effect_id: NotRequired[str]


class CaptionExtra(TypedDict, total=False):
    """
    Правила:
    - message_effect_id учитывается только при отправке в приватных чатах.
    - При edit и/или вне приватных чатов удаляется в процессе нормализации.
    """
    mode: Literal["HTML", "MarkdownV2"]
    entities: NotRequired[list[Entity]]
    message_effect_id: NotRequired[str]


class MediaExtra(TypedDict, total=False):
    """
    Допустимые ключи: spoiler, show_caption_above_media, start, thumb,
    title, performer, duration, width, height.
    """
    spoiler: NotRequired[bool]
    show_caption_above_media: NotRequired[bool]
    start: NotRequired[int]
    thumb: NotRequired[Any]
    title: NotRequired[str]  # audio
    performer: NotRequired[str]  # audio
    duration: NotRequired[int]  # audio/video/animation
    width: NotRequired[int]  # video/animation
    height: NotRequired[int]  # video/animation


Extra = Union[TextExtra, CaptionExtra, MediaExtra]

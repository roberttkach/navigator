from __future__ import annotations

from typing import TypedDict, NotRequired, Literal, Any, Union


Entity = TypedDict(
    "Entity",
    {
        "type": Literal[
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
        ],
        "offset": int,
        "length": int,
        "url": NotRequired[str],
        "user": NotRequired[Any],
        "language": NotRequired[str],
        "custom_emoji_id": NotRequired[str],
    },
    total=False,
)


# Text and caption extras strip message_effect_id outside private chats or during edits.
TextExtra = TypedDict(
    "TextExtra",
    {
        "mode": Literal["HTML", "MarkdownV2"],
        "entities": NotRequired[list[Entity]],
        "message_effect_id": NotRequired[str],
    },
    total=False,
)


CaptionExtra = TypedDict(
    "CaptionExtra",
    {
        "mode": Literal["HTML", "MarkdownV2"],
        "entities": NotRequired[list[Entity]],
        "message_effect_id": NotRequired[str],
    },
    total=False,
)


# Media extras support spoiler/show_caption_above_media/start/thumb/title/performer/
# duration/width/height plus cover/supports_streaming.
MediaExtra = TypedDict(
    "MediaExtra",
    {
        "spoiler": NotRequired[bool],
        "show_caption_above_media": NotRequired[bool],
        "start": NotRequired[int],
        "thumb": NotRequired[Any],
        "title": NotRequired[str],
        "performer": NotRequired[str],
        "duration": NotRequired[int],
        "width": NotRequired[int],
        "height": NotRequired[int],
        "cover": NotRequired[Any],
        "supports_streaming": NotRequired[bool],
    },
    total=False,
)


Extra = Union[TextExtra, CaptionExtra, MediaExtra]

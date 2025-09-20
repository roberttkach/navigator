from navigator.adapters.telegram.serializer import caption_for_edit
from navigator.domain.entity.media import MediaItem, MediaType
from navigator.domain.value.content import Payload


_DEF_MEDIA = MediaItem(type=MediaType.PHOTO, path="file-id")


def test_caption_for_edit_returns_empty_when_marker_present():
    payload = Payload(text="", media=_DEF_MEDIA, erase=True)

    assert caption_for_edit(payload) == ""


def test_caption_for_edit_ignores_empty_text_without_marker():
    payload = Payload(text="", media=_DEF_MEDIA, erase=False)

    assert caption_for_edit(payload) is None


def test_caption_for_edit_prefers_caption_text():
    payload = Payload(text="  actual  ", media=_DEF_MEDIA, erase=False)

    assert caption_for_edit(payload) == "actual"

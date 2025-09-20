import pytest

from navigator.application.dto.content import Content, Media
from navigator.application.map.payload import to_payload


def test_to_payload_marks_erase_for_media():
    dto = Content(text=None, media=Media(path="photo.jpg"), erase=True)

    payload = to_payload(dto)

    assert payload.text == ""
    assert payload.erase is True


def test_to_payload_keeps_erase_with_explicit_empty_text():
    dto = Content(text="", media=Media(path="photo.jpg"), erase=True)

    payload = to_payload(dto)

    assert payload.text == ""
    assert payload.erase is True


def test_to_payload_rejects_legacy_empty_caption_without_flag():
    dto = Content(text="", media=Media(path="photo.jpg"), erase=False)

    with pytest.raises(ValueError, match="empty_caption_without_erase_flag"):
        to_payload(dto)

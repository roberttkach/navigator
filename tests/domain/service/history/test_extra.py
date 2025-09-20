from navigator.domain.service.history.extra import sanitize_extra


def test_sanitize_extra_returns_none_for_non_dict():
    assert sanitize_extra(None, text_len=10) is None
    assert sanitize_extra([], text_len=10) is None  # type: ignore[arg-type]


def test_sanitize_extra_filters_unknown_keys_and_tracks_thumb():
    extra = {
        "mode": "HTML",
        "spoiler": True,
        "thumb": "file_id",
        "unexpected": 42,
    }

    sanitized = sanitize_extra(extra, text_len=0)

    assert sanitized == {"mode": "HTML", "spoiler": True, "has_thumb": True}


def test_sanitize_extra_validates_entities_against_text_length():
    extra = {
        "mode": "HTML",
        "entities": [
            {"type": "bold", "offset": 0, "length": 4},
            {"type": "italic", "offset": 10, "length": 100},
            {
                "type": "text_link",
                "offset": 1,
                "length": 3,
                "url": "https://example.com",
            },
            {"type": "unsupported", "offset": 0, "length": 1},
        ],
    }

    sanitized = sanitize_extra(extra, text_len=6)

    assert sanitized["entities"] == [
        {"type": "bold", "offset": 0, "length": 4},
        {"type": "text_link", "offset": 1, "length": 3, "url": "https://example.com"},
    ]


def test_sanitize_extra_drops_entities_if_none_valid_and_returns_none():
    extra = {"entities": [{"type": "bold", "offset": 0, "length": 10}]}

    assert sanitize_extra(extra, text_len=5) is None

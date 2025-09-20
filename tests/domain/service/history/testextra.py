from navigator.domain.service.history.extra import cleanse


def testNullity():
    assert cleanse(None, length=10) is None
    assert cleanse([], length=10) is None  # type: ignore[arg-type]


def testFiltration():
    extra = {
        "mode": "HTML",
        "spoiler": True,
        "thumb": "file_id",
        "unexpected": 42,
    }

    cleansed = cleanse(extra, length=0)

    assert cleansed == {"mode": "HTML", "spoiler": True, "has_thumb": True}


def testEntities():
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

    cleansed = cleanse(extra, length=6)

    assert cleansed["entities"] == [
        {"type": "bold", "offset": 0, "length": 4},
        {"type": "text_link", "offset": 1, "length": 3, "url": "https://example.com"},
    ]


def testVanish():
    extra = {"entities": [{"type": "bold", "offset": 0, "length": 10}]}

    assert cleanse(extra, length=5) is None

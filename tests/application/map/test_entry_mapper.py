import pytest

from navigator.application.map.entry import EntryMapper, NodeResult
from navigator.domain.entity.media import MediaItem, MediaType
from navigator.domain.value.content import Payload


class DummyRegistry:
    def __init__(self, known: set[str] | None = None) -> None:
        self._known = set(known or [])

    def has(self, key: str) -> bool:  # pragma: no cover - interface stub
        return key in self._known

    def get(self, key: str):  # pragma: no cover - interface stub
        raise NotImplementedError(key)


def make_mapper() -> EntryMapper:
    return EntryMapper(DummyRegistry({"view"}))


def test_entry_mapper_requires_kind_metadata() -> None:
    mapper = make_mapper()
    result = NodeResult(ids=[1], extras=[[]], metas=[{}])

    with pytest.raises(ValueError, match="meta_missing_kind"):
        mapper.from_node_result(result, [Payload(text="hello")], state=None, view=None, root=False)


def test_entry_mapper_rejects_unknown_kind() -> None:
    mapper = make_mapper()
    result = NodeResult(ids=[1], extras=[[]], metas=[{"kind": "unknown"}])

    with pytest.raises(ValueError, match="meta_unsupported_kind"):
        mapper.from_node_result(result, [Payload(text="hello")], state=None, view=None, root=False)


def test_entry_mapper_maps_text_metadata() -> None:
    mapper = make_mapper()
    payload = Payload(text="payload")
    result = NodeResult(
        ids=[1],
        extras=[[]],
        metas=[{"kind": "text", "text": "meta", "inline_id": "123"}],
    )

    entry = mapper.from_node_result(result, [payload], state="s", view="view", root=True)

    assert entry.view == "view"
    assert entry.messages[0].text == "meta"
    assert entry.messages[0].media is None
    assert entry.messages[0].group is None
    assert entry.messages[0].inline_id == "123"


def test_entry_mapper_maps_media_metadata() -> None:
    mapper = make_mapper()
    payload = Payload(media=MediaItem(type=MediaType.PHOTO, path="local", caption="payload"))
    result = NodeResult(
        ids=[5],
        extras=[[42]],
        metas=[{
            "kind": "media",
            "media_type": "photo",
            "file_id": "file-id",
            "caption": "meta caption",
            "inline_id": "inline",
        }],
    )

    entry = mapper.from_node_result(result, [payload], state=None, view=None, root=False)

    msg = entry.messages[0]
    assert msg.media is not None
    assert msg.media.type is MediaType.PHOTO
    assert msg.media.path == "file-id"
    assert msg.media.caption == "meta caption"
    assert msg.text is None
    assert msg.group is None
    assert msg.inline_id == "inline"
    assert msg.aux_ids == [42]


def test_entry_mapper_maps_group_metadata() -> None:
    mapper = make_mapper()
    payload = Payload(
        group=[
            MediaItem(type=MediaType.PHOTO, path="local-a", caption="cap-a"),
            MediaItem(type=MediaType.VIDEO, path="local-b", caption=""),
        ]
    )
    result = NodeResult(
        ids=[9],
        extras=[[]],
        metas=[{
            "kind": "group",
            "group_items": [
                {"media_type": "photo", "file_id": "f1", "caption": "c1"},
                {"media_type": "video", "file_id": "f2", "caption": ""},
            ],
            "inline_id": None,
        }],
    )

    entry = mapper.from_node_result(result, [payload], state=None, view=None, root=False)

    msg = entry.messages[0]
    assert msg.group is not None
    assert [item.type for item in msg.group] == [MediaType.PHOTO, MediaType.VIDEO]
    assert [item.path for item in msg.group] == ["f1", "f2"]
    assert [item.caption for item in msg.group] == ["c1", ""]
    assert msg.media is None
    assert msg.text is None

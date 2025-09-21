import sys
from pathlib import Path
from datetime import datetime, timezone

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from navigator.adapters.storage.historyrepo import HistoryRepo
from navigator.domain.entity.history import Entry, Msg


def test_to_dict_uses_canonical_keys():
    repo = HistoryRepo(state=None)
    msg = Msg(
        id=42,
        text="hello",
        media=None,
        group=None,
        markup=None,
        preview=None,
        extra={"foo": "bar"},
        extras=[1, 2],
        inline="inline-message",
        automated=False,
        ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    entry = Entry(state="s", view="v", messages=[msg], root=True)

    payload = repo._to_dict(entry)
    assert payload["root"] is True
    assert payload["state"] == "s"
    assert payload["view"] == "v"

    serialized_msg = payload["messages"][0]
    assert serialized_msg["extras"] == [1, 2]
    assert serialized_msg["inline"] == "inline-message"
    assert serialized_msg["automated"] is False
    assert "aux_ids" not in serialized_msg
    assert "inline_id" not in serialized_msg
    assert "by_bot" not in serialized_msg


def test_from_dict_reads_canonical_keys():
    repo = HistoryRepo(state=None)
    data = {
        "state": "s",
        "view": "v",
        "root": True,
        "messages": [
            {
                "id": 7,
                "text": "hello",
                "extras": [3, "4"],
                "inline": "inline",
                "automated": False,
                "ts": "2024-01-01T00:00:00.000Z",
            }
        ],
    }

    entry = repo._from_dict(data)
    assert entry.state == "s"
    assert entry.view == "v"
    assert entry.root is True
    assert len(entry.messages) == 1

    msg = entry.messages[0]
    assert msg.id == 7
    assert msg.text == "hello"
    assert msg.extras == [3, 4]
    assert msg.inline == "inline"
    assert msg.automated is False


def test_from_dict_ignores_legacy_keys():
    repo = HistoryRepo(state=None)
    data = {
        "state": "s",
        "view": "v",
        "messages": [
            {
                "id": 1,
                "aux_ids": [9],
                "inline_id": "legacy",
                "by_bot": False,
                "ts": "2024-01-01T00:00:00.000Z",
            }
        ],
    }

    entry = repo._from_dict(data)
    assert len(entry.messages) == 1
    msg = entry.messages[0]
    assert msg.extras == []
    assert msg.inline is None
    assert msg.automated is True

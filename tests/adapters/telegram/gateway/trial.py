import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[4].parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from navigator.adapters.storage.chronicle import Chronicle
from navigator.adapters.telegram.gateway import util as gateway
from navigator.domain.value.message import Scope


def _chronicle_message_payload(**overrides):
    payload = {
        "id": 101,
        "text": "hello",
        "media": None,
        "group": None,
        "markup": None,
        "preview": None,
        "extra": None,
        "extras": [202, 303],
        "inline": None,
        "automated": True,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    return payload


def _chronicle_entry_payload(message):
    return {"state": "state", "view": "view", "messages": [message]}


def digest():
    grouped = SimpleNamespace(media_group_id="group", text="ignored")

    with pytest.raises(ValueError):
        gateway._digest(grouped)

    message = SimpleNamespace(media_group_id=None, text="hello")
    assert gateway._digest(message) == {"kind": "text", "text": "hello", "inline": None}

    chronicle = Chronicle(state=None)

    entry = chronicle._load(
        _chronicle_entry_payload(
            _chronicle_message_payload(),
        )
    )
    assert entry.messages[0].id == 101
    assert entry.messages[0].extras == [202, 303]

    entry_with_inline_id = chronicle._load(
        _chronicle_entry_payload(
            _chronicle_message_payload(inline_id="ignored-inline"),
        )
    )
    assert entry_with_inline_id.messages[0].id == 101
    assert entry_with_inline_id.messages[0].extras == [202, 303]

    missing_id = _chronicle_message_payload()
    missing_id.pop("id")
    with pytest.raises(ValueError, match="missing required 'id'"):
        chronicle._load(_chronicle_entry_payload(missing_id))

    with pytest.raises(ValueError, match="invalid 'id'"):
        chronicle._load(_chronicle_entry_payload(_chronicle_message_payload(id="oops")))

    with pytest.raises(ValueError, match="invalid 'ts'"):
        chronicle._load(
            _chronicle_entry_payload(_chronicle_message_payload(ts="bad timestamp"))
        )

    with pytest.raises(ValueError, match="invalid 'ts'"):
        chronicle._load(
            _chronicle_entry_payload(_chronicle_message_payload(ts=None))
        )


def extract():
    scope = Scope(chat=123)
    payload = SimpleNamespace(group=[object()])

    with pytest.raises(AssertionError):
        gateway.extract(SimpleNamespace(), payload, scope)

    chronicle = Chronicle(state=None)

    with pytest.raises(ValueError, match="non-integer 'extras' entry"):
        chronicle._load(
            _chronicle_entry_payload(_chronicle_message_payload(extras=[1, "oops"]))
        )

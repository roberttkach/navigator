import asyncio
import sys
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from navigator.composition.migrate import cleanse
from navigator.adapters.storage.keys import FSM_HISTORY_KEY


class DummyRegistry:
    def has(self, key: str) -> bool:
        return True


class DummyState:
    def __init__(self, data):
        self._data = data
        self.updates: list[dict] = []

    async def get_data(self):
        return self._data

    async def update_data(self, payload):
        self.updates.append(payload)
        self._data.update(payload)


def test_cleanse_normalizes_history_entries():
    history = [
        {
            "state": "s1",
            "view": "kept_view",
            "messages": [
                {
                    "id": 1,
                    "aux_ids": [1, 2],
                    "inline_id": "inline-val",
                    "by_bot": False,
                },
                {
                    "id": 2,
                    "extras": [9],
                    "inline": "existing-inline",
                    "inline_id": "legacy-inline",
                    "automated": False,
                    "by_bot": True,
                },
            ],
        }
    ]
    state = DummyState({FSM_HISTORY_KEY: history})

    asyncio.run(cleanse(state, registry=DummyRegistry()))

    assert state.updates, "cleanse should persist normalised history"

    stored = state._data[FSM_HISTORY_KEY]
    first_message = stored[0]["messages"][0]
    assert first_message["extras"] == [1, 2]
    assert first_message["inline"] == "inline-val"
    assert first_message["automated"] is False
    assert "aux_ids" not in first_message
    assert "inline_id" not in first_message
    assert "by_bot" not in first_message

    second_message = stored[0]["messages"][1]
    assert second_message["extras"] == [9]
    assert second_message["inline"] == "existing-inline"
    assert second_message["automated"] is False
    assert "inline_id" not in second_message
    assert "by_bot" not in second_message

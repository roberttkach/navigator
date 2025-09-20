from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from navigator.adapters.storage.historyrepo import HistoryRepo
from navigator.adapters.storage.keys import FSM_HISTORY_KEY
from navigator.domain.entity.history import Entry, Msg


class FakeFSMContext:
    def __init__(self) -> None:
        self.data: dict[str, object] = {}

    async def get_data(self) -> dict[str, object]:
        return dict(self.data)

    async def update_data(self, data: dict[str, object]) -> None:
        self.data.update(data)


def test_history_repo_persists_extra_without_mutation() -> None:
    async def scenario() -> None:
        state = FakeFSMContext()
        repo = HistoryRepo(state)  # type: ignore[arg-type]

        msg = Msg(
            id=1,
            text="hello",
            media=None,
            group=None,
            markup=None,
            preview=None,
            extra={"unexpected": "value"},
            aux_ids=[],
            inline_id=None,
            by_bot=True,
            ts=datetime.now(timezone.utc),
        )
        entry = Entry(state="state", view="view", messages=[msg], root=False)

        await repo.save_history([entry])

        stored_payload = state.data[FSM_HISTORY_KEY][0]["messages"][0]["extra"]
        assert stored_payload == {"unexpected": "value"}

        loaded = await repo.get_history()
        assert loaded[0].messages[0].extra == {"unexpected": "value"}
        assert loaded[0].messages[0].text == "hello"

    asyncio.run(scenario())

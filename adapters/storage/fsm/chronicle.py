from __future__ import annotations

from typing import List

from navigator.core.entity.history import Entry
from navigator.core.telemetry import Telemetry

from .chronicle_serializer import HistorySerializer
from .chronicle_storage import ChronicleNamespace, ChronicleStorage
from .chronicle_telemetry import ChronicleTelemetry
from .context import StateContext


class Chronicle:
    """Coordinate chronicle storage, serialisation and telemetry reporting."""

    def __init__(
        self,
        state: StateContext,
        telemetry: Telemetry | None = None,
        *,
        storage: ChronicleStorage | None = None,
        serializer: HistorySerializer | None = None,
        emitter: ChronicleTelemetry | None = None,
    ) -> None:
        self._storage = storage or ChronicleStorage(state)
        self._telemetry = emitter or ChronicleTelemetry(telemetry)
        self._serializer = serializer or HistorySerializer(telemetry)

    async def recall(self) -> List[Entry]:
        namespace = await self._storage.read()
        raw = namespace.history()
        self._telemetry.loaded(len(raw))
        return [
            self._serializer.load(record, self._telemetry)
            for record in raw
            if isinstance(record, dict)
        ]

    async def archive(self, history: List[Entry]) -> None:
        payload = [self._serializer.dump(entry) for entry in history]
        namespace = await self._storage.read()
        namespace.update_history(payload)
        await self._storage.write(namespace)
        self._telemetry.saved(len(payload))


__all__ = ["Chronicle", "ChronicleNamespace", "ChronicleStorage", "ChronicleTelemetry", "HistorySerializer"]

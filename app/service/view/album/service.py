"""Album reconciliation service wiring planner and mutation executor."""

from __future__ import annotations

import logging
from typing import Optional

from navigator.core.entity.history import Message
from navigator.core.port.limits import Limits
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.typing.result import GroupMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..executor import EditExecutor
from .mutations import AlbumMutationExecutor
from .planner import AlbumRefreshPlan, AlbumRefreshPlanner


class AlbumService:
    """Refresh album state and emit edits when existing nodes diverge."""

    def __init__(
        self,
        executor: EditExecutor,
        *,
        limits: Limits,
        thumbguard: bool,
        telemetry: Telemetry,
        planner: AlbumRefreshPlanner | None = None,
        mutations: AlbumMutationExecutor | None = None,
    ) -> None:
        self._planner = planner or AlbumRefreshPlanner(limits=limits, thumbguard=thumbguard)
        self._mutations = mutations or AlbumMutationExecutor(executor)
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def refresh(
        self,
        scope: Scope,
        former: Message,
        latter: Payload,
    ) -> Optional[tuple[int, list[int], GroupMeta, bool]]:
        plan: AlbumRefreshPlan | None = self._planner.prepare(former, latter)
        if plan is None:
            return None

        mutated = await self._mutations.apply(scope, plan.mutations)

        self._channel.emit(
            logging.INFO,
            LogCode.ALBUM_PARTIAL_OK,
            count=len(plan.lineup),
        )

        return plan.lineup[0], plan.extras, plan.meta, mutated


__all__ = ["AlbumService"]

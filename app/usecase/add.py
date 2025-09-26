"""Coordinate history append operations with view updates."""

from __future__ import annotations

import logging
from typing import List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from dataclasses import dataclass

from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload
from ...core.value.message import Scope
from .add_components import (
    AppendEntryAssembler,
    AppendHistoryAccess,
    AppendHistoryWriter,
    AppendPayloadAdapter,
    AppendRenderPlanner,
)


@dataclass(frozen=True)
class AppendDependencies:
    history: AppendHistoryAccess
    payloads: AppendPayloadAdapter
    planner: AppendRenderPlanner
    assembler: AppendEntryAssembler
    writer: AppendHistoryWriter


class Appender:
    """Manage append operations against conversation history."""

    def __init__(
            self,
            *,
            telemetry: Telemetry,
            dependencies: AppendDependencies,
    ) -> None:
        self._history = dependencies.history
        self._payloads = dependencies.payloads
        self._planner = dependencies.planner
        self._assembler = dependencies.assembler
        self._writer = dependencies.writer
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    @classmethod
    def build(
            cls,
            *,
            telemetry: Telemetry,
            history: AppendHistoryAccess,
            payloads: AppendPayloadAdapter,
            planner: AppendRenderPlanner,
            assembler: AppendEntryAssembler,
            writer: AppendHistoryWriter,
    ) -> "Appender":
        dependencies = AppendDependencies(
            history=history,
            payloads=payloads,
            planner=planner,
            assembler=assembler,
            writer=writer,
        )
        return cls(telemetry=telemetry, dependencies=dependencies)

    async def execute(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            root: bool = False,
    ) -> None:
        """Append ``bundle`` to ``scope`` while respecting ``view`` hints."""

        await self._trace.run(
            events.APPEND,
            self._perform,
            scope,
            bundle,
            view,
            root=root,
        )

    async def _perform(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            *,
            root: bool = False,
    ) -> None:
        adjusted = self._payloads.normalize(scope, bundle)
        records = await self._history.snapshot(scope)
        trail = records[-1] if records else None
        render = await self._planner.plan(scope, adjusted, trail)
        if not render or not render.ids or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="add")
            return
        status = await self._history.status()

        entry = self._assembler.build_entry(adjusted, render, status, view, root)
        timeline = self._assembler.extend_timeline(records, entry, root)
        await self._writer.persist(timeline)

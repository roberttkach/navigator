"""Coordinate history append operations with view updates."""

from __future__ import annotations

import logging
from typing import List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from dataclasses import dataclass

from ...core.entity.history import Entry
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
from .render_contract import RenderOutcome


@dataclass(frozen=True)
class AppendDependencies:
    history: AppendHistoryAccess
    payloads: AppendPayloadAdapter
    planner: AppendRenderPlanner
    assembler: AppendEntryAssembler
    writer: AppendHistoryWriter


@dataclass(frozen=True)
class AppendPipeline:
    """Aggregate preparation, rendering and persistence components."""

    preparation: "AppendPreparation"
    rendering: "AppendRendering"
    persistence: "AppendPersistence"


class AppendPipelineFactory:
    """Create append pipeline stages from declarative dependencies."""

    def __init__(self, dependencies: AppendDependencies) -> None:
        self._dependencies = dependencies

    def create(self, channel: TelemetryChannel) -> AppendPipeline:
        preparation = AppendPreparation(
            self._dependencies.history,
            self._dependencies.payloads,
        )
        rendering = AppendRendering(self._dependencies.planner, channel)
        persistence = AppendPersistence(
            self._dependencies.history,
            self._dependencies.assembler,
            self._dependencies.writer,
        )
        return AppendPipeline(
            preparation=preparation,
            rendering=rendering,
            persistence=persistence,
        )


@dataclass(frozen=True)
class AppendPreparationResult:
    """Collect data required for later append pipeline stages."""

    adjusted: List[Payload]
    records: List[Entry]
    trail: Entry | None


class AppendPreparation:
    """Prepare normalized payload bundles and history snapshots."""

    def __init__(self, history: AppendHistoryAccess, payloads: AppendPayloadAdapter) -> None:
        self._history = history
        self._payloads = payloads

    async def prepare(self, scope: Scope, bundle: List[Payload]) -> AppendPreparationResult:
        adjusted = self._payloads.normalize(scope, bundle)
        records = await self._history.snapshot(scope)
        trail = records[-1] if records else None
        return AppendPreparationResult(adjusted=adjusted, records=records, trail=trail)


class AppendRendering:
    """Coordinate render planning and skip detection."""

    def __init__(self, planner: AppendRenderPlanner, channel: TelemetryChannel) -> None:
        self._planner = planner
        self._channel = channel

    async def plan(
        self,
        scope: Scope,
        prepared: AppendPreparationResult,
    ) -> RenderOutcome | None:
        render = await self._planner.plan(scope, prepared.adjusted, prepared.trail)
        if not render or not render.ids or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="add")
            return None
        return render


class AppendPersistence:
    """Persist append results once rendering succeeds."""

    def __init__(
        self,
        history: AppendHistoryAccess,
        assembler: AppendEntryAssembler,
        writer: AppendHistoryWriter,
    ) -> None:
        self._history = history
        self._assembler = assembler
        self._writer = writer

    async def persist(
        self,
        prepared: AppendPreparationResult,
        render: RenderOutcome,
        view: Optional[str],
        *,
        root: bool = False,
    ) -> None:
        status = await self._history.status()
        entry = self._assembler.build_entry(
            prepared.adjusted,
            render,
            status,
            view,
            root,
        )
        timeline = self._assembler.extend_timeline(prepared.records, entry, root)
        await self._writer.persist(timeline)


class Appender:
    """Manage append operations against conversation history."""

    def __init__(
        self,
        *,
        telemetry: Telemetry,
        factory: AppendPipelineFactory,
    ) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)
        pipeline = factory.create(self._channel)
        self._preparation = pipeline.preparation
        self._rendering = pipeline.rendering
        self._persistence = pipeline.persistence

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
        factory = AppendPipelineFactory(dependencies)
        return cls(telemetry=telemetry, factory=factory)

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
        prepared = await self._preparation.prepare(scope, bundle)
        render = await self._rendering.plan(scope, prepared)
        if render is None:
            return
        await self._persistence.persist(prepared, render, view, root=root)

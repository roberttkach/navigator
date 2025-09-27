"""Coordinate history append operations with view updates."""

from __future__ import annotations

import logging
from typing import List, Optional

from dataclasses import dataclass

from ..log import events
from ..log.aspect import TraceAspect

from ...core.entity.history import Entry
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload
from ...core.value.message import Scope
from .add_components import (
    AppendEntryAssembler,
    AppendHistoryWriter,
    AppendPayloadAdapter,
    AppendRenderPlanner,
    HistorySnapshotAccess,
    StateStatusAccess,
)
from .render_contract import RenderOutcome


@dataclass(frozen=True)
class AppendDependencies:
    history: HistorySnapshotAccess
    state: StateStatusAccess
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


@dataclass(frozen=True)
class AppendInstrumentation:
    """Capture telemetry collaborators used during append orchestration."""

    channel: TelemetryChannel
    trace: TraceAspect

    @classmethod
    def from_telemetry(cls, telemetry: Telemetry) -> "AppendInstrumentation":
        return cls(channel=telemetry.channel(__name__), trace=TraceAspect(telemetry))


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
            self._dependencies.state,
            self._dependencies.assembler,
            self._dependencies.writer,
        )
        return AppendPipeline(
            preparation=preparation,
            rendering=rendering,
            persistence=persistence,
        )


class AppendWorkflow:
    """Orchestrate append pipeline execution independently from telemetry."""

    def __init__(self, pipeline: AppendPipeline) -> None:
        self._preparation = pipeline.preparation
        self._rendering = pipeline.rendering
        self._persistence = pipeline.persistence

    @classmethod
    def from_factory(
        cls,
        factory: AppendPipelineFactory,
        channel: TelemetryChannel,
    ) -> "AppendWorkflow":
        return cls(factory.create(channel))

    async def run(
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


@dataclass(frozen=True)
class AppendPreparationResult:
    """Collect data required for later append pipeline stages."""

    adjusted: List[Payload]
    records: List[Entry]
    trail: Entry | None


class AppendPreparation:
    """Prepare normalized payload bundles and history snapshots."""

    def __init__(self, history: HistorySnapshotAccess, payloads: AppendPayloadAdapter) -> None:
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
        state: StateStatusAccess,
        assembler: AppendEntryAssembler,
        writer: AppendHistoryWriter,
    ) -> None:
        self._state = state
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
        status = await self._state.status()
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
        instrumentation: AppendInstrumentation,
        workflow: AppendWorkflow,
    ) -> None:
        self._instrumentation = instrumentation
        self._workflow = workflow

    async def execute(
        self,
        scope: Scope,
        bundle: List[Payload],
        view: Optional[str],
        root: bool = False,
    ) -> None:
        """Append ``bundle`` to ``scope`` while respecting ``view`` hints."""

        await self._instrumentation.trace.run(
            events.APPEND,
            self._workflow.run,
            scope,
            bundle,
            view,
            root=root,
        )

"""Coordinate history append operations with view updates."""

from __future__ import annotations

from typing import List, Optional

from ...core.value.content import Payload
from ...core.value.message import Scope
from .add_instrumentation import AppendInstrumentation
from .add_pipeline import (
    AppendPersistence,
    AppendPersistenceFactory,
    AppendPipeline,
    AppendPipelineFactory,
    AppendPreparation,
    AppendPreparationFactory,
    AppendPreparationResult,
    AppendRendering,
    AppendRenderingFactory,
    AppendWorkflow,
)


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

        await self._instrumentation.traced(
            self._workflow.run,
            scope,
            bundle,
            view,
            root=root,
        )


__all__ = [
    "AppendInstrumentation",
    "AppendPersistence",
    "AppendPersistenceFactory",
    "AppendPipeline",
    "AppendPipelineFactory",
    "AppendPreparation",
    "AppendPreparationFactory",
    "AppendPreparationResult",
    "AppendRendering",
    "AppendRenderingFactory",
    "AppendWorkflow",
    "Appender",
]

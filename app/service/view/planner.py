"""Plan rendering operations that reconcile history with payloads."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from navigator.core.entity.history import Entry, Message
from navigator.core.service.rendering import decision
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.typing.result import Cluster, GroupMeta, MediaMeta, Meta, TextMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope
from typing import List, Optional, Sequence

from .album import AlbumService
from .executor import EditExecutor, Execution
from .inline import InlineHandler, InlineOutcome
from .policy import adapt
from ...internal.policy import shield


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Describe a single gateway result produced during rendering."""

    id: int
    extra: List[int]
    meta: Meta


@dataclass(frozen=True, slots=True)
class RenderNode:
    """Collect identifiers and metadata for a rendered node."""

    ids: List[int]
    extras: List[List[int]]
    metas: List[Meta]
    changed: bool


@dataclass(slots=True)
class _RenderState:
    """Accumulate message identifiers and metadata during planning."""

    ids: List[int] = field(default_factory=list)
    extras: List[List[int]] = field(default_factory=list)
    metas: List[Meta] = field(default_factory=list)

    def retain(self, message: Message) -> None:
        """Record existing message details without triggering mutations."""

        self.ids.append(message.id)
        self.extras.append(list(message.extras or []))
        self.metas.append(_meta(message))

    def collect(self, execution: Execution, meta: Meta) -> None:
        """Capture execution outcome alongside calculated metadata."""

        self.ids.append(execution.result.id)
        self.extras.append(list(execution.result.extra))
        self.metas.append(meta)


def _meta(node: Message) -> Meta:
    """Convert stored history message into lightweight metadata."""

    if node.group:
        return GroupMeta(
            clusters=[
                Cluster(
                    medium=item.type.value,
                    file=item.path,
                    caption=item.caption,
                )
                for item in node.group
            ],
            inline=node.inline,
        )
    if node.media:
        return MediaMeta(
            medium=node.media.type.value,
            file=node.media.path,
            caption=node.media.caption,
            inline=node.inline,
        )
    return TextMeta(text=node.text, inline=node.inline)


class ViewPlanner:
    """Plan edits, deletions, and sends for a desired payload state."""

    def __init__(
            self,
            executor: EditExecutor,
            inline: InlineHandler,
            album: AlbumService,
            rendering: RenderingConfig,
            telemetry: Telemetry,
    ) -> None:
        self._executor = executor
        self._inline = inline
        self._album = album
        self._rendering = rendering
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def render(
            self,
            scope: Scope,
            payloads: Sequence[Payload],
            trail: Optional[Entry],
            *,
            inline: bool,
    ) -> Optional[RenderNode]:
        """Plan rendering actions for ``payloads`` within ``scope``."""

        if inline:
            shield(scope, payloads, inline=True)

        fresh = [adapt(scope, p) for p in payloads]
        ledger = list(trail.messages) if trail else []

        state = _RenderState()
        if inline:
            mutated = await self._render_inline(scope, fresh, ledger, state)
        else:
            mutated = await self._render_regular(scope, fresh, ledger, state)

        if not state.ids:
            return None

        return RenderNode(ids=state.ids, extras=state.extras, metas=state.metas, changed=mutated)

    async def _render_inline(
            self,
            scope: Scope,
            fresh: List[Payload],
            ledger: List[Message],
            state: _RenderState,
    ) -> bool:
        """Reconcile inline payloads with the existing ledger."""

        return await self._sync(
            scope,
            fresh,
            ledger,
            state,
            start=0,
            inline_mode=True,
        )

    async def _render_regular(
            self,
            scope: Scope,
            fresh: List[Payload],
            ledger: List[Message],
            state: _RenderState,
    ) -> bool:
        """Handle regular rendering that may edit, append, or trim history."""

        origin, head_changed = await self._head(scope, ledger, fresh, state)
        mutated = head_changed

        mutated = (
                mutated
                or await self._sync(
            scope,
            fresh,
            ledger,
            state,
            start=origin,
            inline_mode=False,
        )
        )

        stored = len(ledger)
        incoming = len(fresh)
        mutated = mutated or await self._trim(scope, ledger, incoming)
        mutated = mutated or await self._append(scope, fresh, stored, state)
        return mutated

    async def _head(
            self,
            scope: Scope,
            ledger: List[Message],
            fresh: List[Payload],
            state: _RenderState,
    ) -> tuple[int, bool]:
        """Attempt to refresh the leading album message when applicable."""

        if not (
                ledger
                and fresh
                and getattr(ledger[0], "group", None)
                and getattr(fresh[0], "group", None)
        ):
            return 0, False

        album = await self._album.refresh(scope, ledger[0], fresh[0])
        if not album:
            self._channel.emit(logging.INFO, LogCode.ALBUM_PARTIAL_FALLBACK)
            return 0, False

        head, extras, meta, changed = album
        state.ids.append(head)
        state.extras.append(extras)
        state.metas.append(meta)
        return 1, changed

    async def _sync(
            self,
            scope: Scope,
            fresh: List[Payload],
            ledger: List[Message],
            state: _RenderState,
            *,
            start: int,
            inline_mode: bool,
    ) -> bool:
        """Synchronize overlapping history and payload slices."""

        mutated = False
        limit = min(len(ledger), len(fresh))
        for index in range(start, limit):
            previous = ledger[index]
            current = fresh[index]
            verdict = decision.decide(previous, current, self._rendering)

            if verdict is decision.Decision.NO_CHANGE:
                state.retain(previous)
                continue

            if inline_mode:
                changed = await self._mediate(scope, current, previous, state)
                mutated = mutated or self._retain_if_unchanged(changed, previous, state)
                continue

            changed = await self._regular(scope, verdict, current, previous, state)
            mutated = mutated or self._retain_if_unchanged(changed, previous, state)

        return mutated

    async def _mediate(
            self,
            scope: Scope,
            payload: Payload,
            previous: Message,
            state: _RenderState,
    ) -> bool:
        """Apply inline reconciliation using the inline handler pipeline."""

        outcome = await self._inline.handle(
            scope=scope,
            payload=payload,
            tail=previous,
            executor=self._executor,
            config=self._rendering,
        )
        if outcome is None:
            return False
        return self._record(outcome, state)

    @staticmethod
    def _retain_if_unchanged(changed: bool, previous: Message, state: _RenderState) -> bool:
        """Retain ``previous`` when no mutation occurred and propagate flag."""

        if not changed:
            state.retain(previous)
        return changed

    def _record(self, outcome: InlineOutcome, state: _RenderState) -> bool:
        meta = self._executor.refine(outcome.execution, outcome.decision, outcome.payload)
        state.collect(outcome.execution, meta)
        return True

    async def _regular(
            self,
            scope: Scope,
            verdict: decision.Decision,
            payload: Payload,
            previous: Message,
            state: _RenderState,
    ) -> bool:
        """Execute standard reconciliation against the message gateway."""

        execution = await self._executor.execute(scope, verdict, payload, previous)
        if execution is None:
            return False
        meta = self._executor.refine(execution, verdict, payload)
        state.collect(execution, meta)
        return True

    async def _trim(self, scope: Scope, ledger: List[Message], incoming: int) -> bool:
        """Prune stored messages beyond the planned payload length."""

        if len(ledger) <= incoming:
            return False
        targets: List[int] = []
        for message in ledger[incoming:]:
            targets.append(message.id)
            targets.extend(list(message.extras or []))
        if not targets:
            return False
        await self._executor.delete(scope, targets)
        return True

    async def _append(
            self,
            scope: Scope,
            fresh: List[Payload],
            stored: int,
            state: _RenderState,
    ) -> bool:
        """Append new payloads beyond existing history."""

        if len(fresh) <= stored:
            return False
        mutated = False
        for payload in fresh[stored:]:
            verdict = decision.decide(None, payload, self._rendering)
            execution = await self._executor.execute(scope, verdict, payload, None)
            if not execution:
                continue
            meta = self._executor.refine(execution, verdict, payload)
            state.collect(execution, meta)
            mutated = True
        return mutated


__all__ = ["RenderResult", "RenderNode", "ViewPlanner"]

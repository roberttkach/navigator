from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from navigator.core.entity.history import Entry, Message
from navigator.core.service.rendering import decision
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.telemetry import LogCode, telemetry
from navigator.core.typing.result import Cluster, GroupMeta, MediaMeta, Meta, TextMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ...internal.policy import validate_inline
from .album import AlbumService
from .executor import EditExecutor, Execution
from .inline import InlineHandler, InlineOutcome
from .policy import adapt

channel = telemetry.channel(__name__)


@dataclass(frozen=True, slots=True)
class RenderResult:
    id: int
    extra: List[int]
    meta: Meta


@dataclass(frozen=True, slots=True)
class RenderNode:
    ids: List[int]
    extras: List[List[int]]
    metas: List[Meta]
    changed: bool


@dataclass(slots=True)
class _RenderState:
    ids: List[int] = field(default_factory=list)
    extras: List[List[int]] = field(default_factory=list)
    metas: List[Meta] = field(default_factory=list)

    def add_existing(self, message: Message) -> None:
        self.ids.append(message.id)
        self.extras.append(list(message.extras or []))
        self.metas.append(_meta(message))

    def add_execution(self, execution: Execution, meta: Meta) -> None:
        self.ids.append(execution.result.id)
        self.extras.append(list(execution.result.extra))
        self.metas.append(meta)


def _meta(node: Message) -> Meta:
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
    def __init__(
        self,
        executor: EditExecutor,
        inline: InlineHandler,
        album: AlbumService,
        rendering: RenderingConfig,
    ) -> None:
        self._executor = executor
        self._inline = inline
        self._album = album
        self._rendering = rendering

    async def render(
        self,
        scope: Scope,
        payloads: Sequence[Payload],
        trail: Optional[Entry],
        *,
        inline: bool,
    ) -> Optional[RenderNode]:
        if inline:
            validate_inline(scope, payloads, inline=True)

        fresh = [adapt(scope, p) for p in payloads]
        ledger = list(trail.messages) if trail else []

        state = _RenderState()
        mutated = False
        origin = 0

        if not inline:
            origin, changed = await self._apply_album_head(scope, ledger, fresh, state)
            mutated = mutated or changed

        stored = len(ledger)
        incoming = len(fresh)
        mutated = mutated or await self._sync_slots(
            scope,
            fresh,
            ledger,
            state,
            start=origin,
            inline_mode=inline,
        )

        if not inline:
            mutated = mutated or await self._trim_tail(scope, ledger, incoming)
            mutated = mutated or await self._append_missing(scope, fresh, stored, state)

        if not state.ids:
            return None

        return RenderNode(ids=state.ids, extras=state.extras, metas=state.metas, changed=mutated)

    async def _apply_album_head(
        self,
        scope: Scope,
        ledger: List[Message],
        fresh: List[Payload],
        state: _RenderState,
    ) -> tuple[int, bool]:
        if not (
            ledger
            and fresh
            and getattr(ledger[0], "group", None)
            and getattr(fresh[0], "group", None)
        ):
            return 0, False

        album = await self._album.partial_update(scope, ledger[0], fresh[0])
        if not album:
            channel.emit(logging.INFO, LogCode.ALBUM_PARTIAL_FALLBACK)
            return 0, False

        head_id, extras, meta, changed = album
        state.ids.append(head_id)
        state.extras.append(extras)
        state.metas.append(meta)
        return 1, changed

    async def _sync_slots(
        self,
        scope: Scope,
        fresh: List[Payload],
        ledger: List[Message],
        state: _RenderState,
        *,
        start: int,
        inline_mode: bool,
    ) -> bool:
        mutated = False
        limit = min(len(ledger), len(fresh))
        for index in range(start, limit):
            previous = ledger[index]
            current = fresh[index]
            verdict = decision.decide(previous, current, self._rendering)

            if verdict is decision.Decision.NO_CHANGE:
                state.add_existing(previous)
                continue

            if inline_mode:
                changed = await self._apply_inline(scope, current, previous, state)
                if not changed:
                    state.add_existing(previous)
                mutated = mutated or changed
                continue

            changed = await self._apply_regular(scope, verdict, current, previous, state)
            if not changed:
                state.add_existing(previous)
            mutated = mutated or changed

        return mutated

    async def _apply_inline(
        self,
        scope: Scope,
        payload: Payload,
        previous: Message,
        state: _RenderState,
    ) -> bool:
        outcome = await self._inline.handle(
            scope=scope,
            payload=payload,
            tail=previous,
            executor=self._executor,
            config=self._rendering,
        )
        if outcome is None:
            return False
        return self._record_inline(outcome, state)

    def _record_inline(self, outcome: InlineOutcome, state: _RenderState) -> bool:
        meta = self._executor.refine_meta(outcome.execution, outcome.decision, outcome.payload)
        state.add_execution(outcome.execution, meta)
        return True

    async def _apply_regular(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        previous: Message,
        state: _RenderState,
    ) -> bool:
        execution = await self._executor.execute(scope, verdict, payload, previous)
        if execution is None:
            return False
        meta = self._executor.refine_meta(execution, verdict, payload)
        state.add_execution(execution, meta)
        return True

    async def _trim_tail(self, scope: Scope, ledger: List[Message], incoming: int) -> bool:
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

    async def _append_missing(
        self,
        scope: Scope,
        fresh: List[Payload],
        stored: int,
        state: _RenderState,
    ) -> bool:
        if len(fresh) <= stored:
            return False
        mutated = False
        for payload in fresh[stored:]:
            execution = await self._executor.execute(
                scope,
                decision.Decision.RESEND,
                payload,
                None,
            )
            if not execution:
                continue
            meta = self._executor.refine_meta(execution, decision.Decision.RESEND, payload)
            state.add_execution(execution, meta)
            mutated = True
        return mutated


__all__ = ["RenderResult", "RenderNode", "ViewPlanner"]

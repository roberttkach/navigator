from __future__ import annotations

import logging
from dataclasses import dataclass
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
from .executor import EditExecutor
from .inline import InlineStrategy
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
        inline: InlineStrategy,
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

        primary: List[int] = []
        bundles: List[List[int]] = []
        notes: List[Meta] = []
        mutated = False
        origin = 0

        if (
            not inline
            and ledger
            and fresh
            and getattr(ledger[0], "group", None)
            and getattr(fresh[0], "group", None)
        ):
            album = await self._album.partial_update(scope, ledger[0], fresh[0])
            if album:
                head_id, extras, meta, changed = album
                primary.append(head_id)
                bundles.append(extras)
                notes.append(meta)
                mutated = mutated or changed
                origin = 1
            else:
                channel.emit(logging.INFO, LogCode.ALBUM_PARTIAL_FALLBACK)

        stored = len(ledger)
        incoming = len(fresh)
        limit = min(stored, incoming)

        for index in range(origin, limit):
            previous = ledger[index]
            current = fresh[index]
            verdict = decision.decide(previous, current, self._rendering)

            if verdict is decision.Decision.NO_CHANGE:
                primary.append(previous.id)
                bundles.append(list(previous.extras or []))
                notes.append(_meta(previous))
                continue

            if inline:
                outcome = await self._inline.handle(
                    scope=scope,
                    payload=current,
                    tail=previous,
                    executor=self._executor,
                    config=self._rendering,
                )
                if outcome is None:
                    primary.append(previous.id)
                    bundles.append(list(previous.extras or []))
                    notes.append(_meta(previous))
                    continue

                meta = self._executor.refine_meta(
                    outcome.execution,
                    outcome.decision,
                    outcome.payload,
                )
                primary.append(outcome.execution.result.id)
                bundles.append(list(outcome.execution.result.extra))
                notes.append(meta)
                mutated = True
                continue

            execution = await self._executor.execute(scope, verdict, current, previous)
            if execution is None:
                primary.append(previous.id)
                bundles.append(list(previous.extras or []))
                notes.append(_meta(previous))
                continue

            meta = self._executor.refine_meta(execution, verdict, current)
            primary.append(execution.result.id)
            bundles.append(list(execution.result.extra))
            notes.append(meta)
            mutated = True

        if stored > incoming and not inline:
            targets: List[int] = []
            for message in ledger[incoming:]:
                targets.append(message.id)
                targets.extend(list(message.extras or []))
            if targets:
                await self._executor.delete(scope, targets)
                mutated = True

        if incoming > stored and not inline:
            for payload in fresh[stored:]:
                execution = await self._executor.execute(
                    scope,
                    decision.Decision.RESEND,
                    payload,
                    None,
                )
                if execution:
                    meta = self._executor.refine_meta(execution, decision.Decision.RESEND, payload)
                    primary.append(execution.result.id)
                    bundles.append(list(execution.result.extra))
                    notes.append(meta)
                    mutated = True

        if not primary:
            return None

        return RenderNode(ids=primary, extras=bundles, metas=notes, changed=mutated)


__all__ = ["RenderResult", "RenderNode", "ViewPlanner"]

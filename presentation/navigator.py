"""Document Navigator API invariants for inline and history flows.

Message effects (``message_effect_id``)
======================================
* History keeps the effect identifier but Telegram only applies it in
  private chats during new sends.
* Normalization strips effects from edits and from sends to non-private
  chats.
* Changing only the effect without touching text, media, or markup is
  treated as ``NO_CHANGE``.

Inline mode in ``back`` and ``set``
==================================
* Only the first message in the node is eligible for editing.
* The ``InlineTailDelete`` flag controls visual tail deletion (default
  ``False``).

Inline edits without fallback
=============================
* ``EditForbidden`` and ``MessageUnchanged`` in inline mode do not trigger
  ``send+delete`` fallbacks.
* Telemetry marker: ``RERENDER_INLINE_NO_FALLBACK``.

Inline content type restrictions
================================
* Inline mode never switches between media and text payload kinds.
* ``EDIT_MARKUP`` is allowed when only the keyboard changes for an existing
  media message.
* Telemetry marker: ``RENDER_SKIP`` with ``note="inline_no_content_type_switch"``.

``rebase`` with empty history
=============================
* The operation is a no-op and ``last_id`` remains unchanged.

``last.edit`` resend fallback
=============================
* After a resend fallback the history is patched before ``last_id`` is
  updated.

Inline ``DELETE_SEND`` remapping
================================
* Inline ``DELETE_SEND`` becomes ``EDIT_MEDIA``.
* ``DELETE_SEND`` downgrades to ``EDIT_TEXT`` when both sides are textual.
* ``EDIT_MARKUP`` is allowed when the media is left untouched.
* Remapping happens in ``InlineHandler.handle`` and ``Tailer.edit``.
* Telemetry marker: ``INLINE_REMAP_DELETE_SEND``.

Inline ``last.delete`` without business context
===============================================
* Without ``business`` the operation only trims history when
  ``TailPrune`` is ``True``; Telegram messages are left intact.

Inline ``edit_media`` success bookkeeping
=========================================
* When Telegram reports success the latest caption and ``file_id`` are
  stored, preventing restore/back/set operations from using stale data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, SupportsInt, Union

from .alerts import missing
from .types import StateLike
from ..app.dto.content import Content, Node
from ..app.locks.guard import Guardian
from ..app.map.payload import collect, convert
from ..app.usecase.add import Appender
from ..app.usecase.alarm import Alarm
from ..app.usecase.back import Rewinder
from ..app.usecase.last import Tailer
from ..app.usecase.pop import Trimmer
from ..app.usecase.rebase import Shifter
from ..app.usecase.replace import Swapper
from ..app.usecase.set import Setter
from ..core.error import StateNotFound
from ..core.service.scope import profile
from ..core.telemetry import LogCode, Telemetry, TelemetryChannel
from ..core.value.content import Payload
from ..core.value.message import Scope


class _TailView:
    """Expose tail operations guarded by telemetry and locking."""

    def __init__(
            self,
            *,
            flow: Tailer,
            scope: Scope,
            guard: Guardian,
            telemetry: Telemetry,
    ):
        self._tailer = flow
        self._scope = scope
        self._guard = guard
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)

    async def get(self) -> Optional[Dict[str, Any]]:
        self._emit("last.get")
        async with self._guard(self._scope):
            identifier = await self._tailer.peek()
        if identifier is None:
            return None
        return {
            "id": identifier,
            "inline": bool(self._scope.inline),
            "chat": self._scope.chat,
        }

    async def delete(self) -> None:
        self._emit("last.delete")
        async with self._guard(self._scope):
            await self._tailer.delete(self._scope)

    async def edit(self, content: Content) -> Optional[int]:
        self._emit(
            "last.edit",
            payload={
                "text": bool(content.text),
                "media": bool(content.media),
                "group": bool(content.group),
            },
        )
        async with self._guard(self._scope):
            result = await self._tailer.edit(self._scope, convert(content))
        return result

    def _emit(self, method: str, **fields: Any) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


class Navigator:
    def __init__(
            self,
            *,
            appender: Appender,
            swapper: Swapper,
            rewinder: Rewinder,
            setter: Setter,
            trimmer: Trimmer,
            shifter: Shifter,
            tailer: Tailer,
            alarm: Alarm,
            scope: Scope,
            guard: Guardian,
            telemetry: Telemetry,
    ):
        self._appender = appender
        self._swapper = swapper
        self._rewinder = rewinder
        self._setter = setter
        self._trimmer = trimmer
        self._shifter = shifter
        self._tailer = tailer
        self._alarm = alarm
        self._scope = scope
        self._guard = guard
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)
        self.last = _TailView(flow=tailer, scope=scope, guard=guard, telemetry=telemetry)

    async def add(self, content: Union[Content, Node], *, key: Optional[str] = None, root: bool = False) -> None:
        payloads = self._bundle(content)
        self._report(
            "add",
            key=key,
            root=root,
            payload={"count": len(payloads)},
        )
        async with self._guard(self._scope):
            await self._appender.execute(self._scope, payloads, key, root=root)

    async def replace(self, content: Union[Content, Node]) -> None:
        payloads = self._bundle(content)
        self._report(
            "replace",
            payload={"count": len(payloads)},
        )
        async with self._guard(self._scope):
            await self._swapper.execute(self._scope, payloads)

    async def rebase(self, message: int | SupportsInt) -> None:
        identifier = getattr(message, "id", message)
        self._report("rebase", message={"id": int(identifier)})
        async with self._guard(self._scope):
            await self._shifter.execute(int(identifier))

    async def back(self, context: Dict[str, Any]) -> None:
        handlers = sorted(list(context.keys())) if isinstance(context, dict) else None
        self._report("back", handlers=handlers)
        async with self._guard(self._scope):
            await self._rewinder.execute(self._scope, context)

    async def set(self, state: Union[str, StateLike], context: Dict[str, Any] | None = None) -> None:
        status = getattr(state, "state", state)
        self._report("set", state=status)
        async with self._guard(self._scope):
            try:
                await self._setter.execute(self._scope, status, context or {})
            except StateNotFound:
                await self._alarm.execute(self._scope, text=missing(self._scope))

    async def pop(self, count: int = 1) -> None:
        self._report("pop", count=count)
        async with self._guard(self._scope):
            await self._trimmer.execute(count)

    async def alert(self) -> None:
        self._report("alert")
        async with self._guard(self._scope):
            await self._alarm.execute(self._scope)

    def _bundle(self, content: Union[Content, Node]) -> List[Payload]:
        node = content if isinstance(content, Node) else Node(messages=[content])
        return collect(node)

    def _report(self, method: str, **fields: Any) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )

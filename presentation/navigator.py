"""
Navigator API — ключевые контракты:

1) Эффекты сообщений (message_effect_id):
   - Хранится в истории.
   - Применяется только при отправке в приватных чатах.
   - При edit и/или вне приватных чатов эффект удаляется нормализацией.
   - Попытка «поменять только эффект» (без изменения текста/медиа/markup) = NO_CHANGE.

2) Inline-режим в back/set:
   - Редактируется только первое сообщение узла.
   - Визуальное удаление «хвоста» контролируется флагом InlineTailDelete (по умолчанию False).

3) Inline-редакции без фоллбека:
   - При EditForbidden/MessageUnchanged в inline не выполняется send+delete.
   - Лог-маркер: RERENDER_INLINE_NO_FALLBACK.

4) Inline: запрет смены типа контента:
   - Смена «медиа ↔ текст» в inline не выполняется.
   - Разрешено только EDIT_MARKUP над существующим медиа при изменении клавиатуры.
   - Иначе: RENDER_SKIP (note="inline_no_content_type_switch").

5) Rebase при пустой истории:
   - Операция no-op, last_id не изменяется.

6) last.edit resend-fallback:
   - После resend история патчится и только затем обновляется last_id.

7) effect_stripped:
   - При нормализации extra эффект сообщения удаляется при edit и/или вне приватных чатов.
   - В логах помечается note="effect_stripped".

8) Inline: ремап DELETE_SEND:
   - В inline DELETE_SEND ремапится в EDIT_MEDIA; в EDIT_TEXT — только когда база и новый — текст.
   - Если медиа не редактируется, но меняется только клавиатура — допускается EDIT_MARKUP.
    - Точки ремапа: InlineHandler.handle и Tailer.edit.
   - Лог-маркер: INLINE_REMAP_DELETE_SEND.

9) Inline: last.delete без business — удаляет только из истории при TailPrune=True.
   Удаления в Telegram не выполняются.

10) Inline: при edit_media, когда Telegram возвращает True, история фиксирует актуальную подпись и новый file_id
    (если в payload.media.path передан строковый file_id). Это исключает устаревание caption/file_id в restore/back/set.
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, Union, SupportsInt

from ..app.dto.content import Content, Node
from ..app.map.payload import collect, convert
from ..app.usecase.add import Appender
from ..app.usecase.alarm import Alarm
from ..app.usecase.back import Rewinder
from ..app.usecase.last import Tailer
from ..app.usecase.pop import Trimmer
from ..app.usecase.rebase import Shifter
from ..app.usecase.replace import Swapper
from ..app.usecase.set import Setter
from ..app.locks.guard import GuardFactory
from ..core.error import StateNotFound
from ..core.service.scope import profile
from ..core.telemetry import LogCode, Telemetry, TelemetryChannel
from ..core.value.message import Scope
from .alerts import prev_not_found
from .types import StateLike


class _Tail:
    def __init__(
        self,
        flow: Tailer,
        scope: Scope,
        guard: GuardFactory,
        telemetry: Telemetry,
    ):
        self._tailer = flow
        self._scope = scope
        self._guard = guard
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def get(self) -> Optional[Dict[str, Any]]:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="last.get",
            scope=profile(self._scope),
        )
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
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="last.delete",
            scope=profile(self._scope),
        )
        async with self._guard(self._scope):
            await self._tailer.delete(self._scope)

    async def edit(self, content: Content) -> Optional[int]:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="last.edit",
            scope=profile(self._scope),
            payload={"text": bool(content.text), "media": bool(content.media), "group": bool(content.group)},
        )
        async with self._guard(self._scope):
            result = await self._tailer.edit(self._scope, convert(content))
        return result


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
            guard: GuardFactory,
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
        self.last = _Tail(flow=tailer, scope=scope, guard=guard, telemetry=telemetry)

    async def add(self, content: Union[Content, Node], *, key: Optional[str] = None, root: bool = False) -> None:
        node = content if isinstance(content, Node) else Node(messages=[content])
        payloads = collect(node)
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="add",
            scope=profile(self._scope),
            key=key,
            root=root,
            payload={"count": len(payloads)},
        )
        async with self._guard(self._scope):
            await self._appender.execute(self._scope, payloads, key, root=root)

    async def replace(self, content: Union[Content, Node]) -> None:
        node = content if isinstance(content, Node) else Node(messages=[content])
        payloads = collect(node)
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="replace",
            scope=profile(self._scope),
            payload={"count": len(payloads)},
        )
        async with self._guard(self._scope):
            await self._swapper.execute(self._scope, payloads)

    async def rebase(self, message: int | SupportsInt) -> None:
        identifier = getattr(message, "id", message)
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="rebase",
            scope=profile(self._scope),
            message={"id": int(identifier)},
        )
        async with self._guard(self._scope):
            await self._shifter.execute(int(identifier))

    async def back(self, context: Dict[str, Any]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="back",
            scope=profile(self._scope),
            handlers=sorted(list(context.keys())) if isinstance(context, dict) else None,
        )
        async with self._guard(self._scope):
            await self._rewinder.execute(self._scope, context)

    async def set(self, state: Union[str, StateLike], context: Dict[str, Any] | None = None) -> None:
        status = getattr(state, "state", state)
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="set",
            scope=profile(self._scope),
            state=status,
        )
        async with self._guard(self._scope):
            try:
                await self._setter.execute(self._scope, status, context or {})
            except StateNotFound:
                await self._alarm.execute(self._scope, text=prev_not_found(self._scope))

    async def pop(self, count: int = 1) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="pop",
            scope=profile(self._scope),
            count=count,
        )
        async with self._guard(self._scope):
            await self._trimmer.execute(count)

    async def alert(self) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="alert",
            scope=profile(self._scope),
        )
        async with self._guard(self._scope):
            await self._alarm.execute(self._scope)


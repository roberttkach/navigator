"""
Navigator API — ключевые контракты:

1) Эффекты сообщений (message_effect_id):
   - Хранится в истории.
   - Применяется только при отправке в приватных чатах.
   - При edit и/или вне приватных чатов эффект удаляется нормализацией.
   - Попытка «поменять только эффект» (без изменения текста/медиа/markup) = NO_CHANGE.

2) Inline-режим в back/set:
   - Редактируется только первое сообщение узла.
   - «Хвост» из нескольких сообщений не удаляется визуально. Это ожидаемое поведение.

3) Inline-редакции без фоллбека:
   - При MessageEditForbidden/NotChanged в inline не выполняется send+delete.
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
   - Точки ремапа: InlineStrategy.handle_element и LastUseCase.edit.
   - Лог-маркер: INLINE_REMAP_DELETE_SEND.

9) Inline: last.delete без biz_id — удаляет только из истории при INLINE_DELETE_TRIMS_HISTORY=True.
   Удаления в Telegram не выполняются.

10) Inline: при edit_media, когда Telegram возвращает True, история фиксирует актуальную подпись и новый file_id
    (если в payload.media.path передан строковый file_id). Это исключает устаревание caption/file_id в restore/back/set.
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, Union, SupportsInt

from ..application import locks
from ..application.dto.content import Content, Node
from ..application.log.emit import jlog
from ..application.map.payload import to_node_payload, to_payload
from ..application.usecase.add import AddUseCase
from ..application.usecase.back import BackUseCase
from ..application.usecase.last import LastUseCase
from ..application.usecase.notify_history_empty import NotifyHistoryEmptyUseCase
from ..application.usecase.pop import PopUseCase
from ..application.usecase.rebase import RebaseUseCase
from ..application.usecase.replace import ReplaceUseCase
from ..application.usecase.set import SetUseCase
from ..domain.service.scope import scope_kv
from ..domain.value.message import Scope
from ..logging.code import LogCode
from .types import StateLike

logger = logging.getLogger(__name__)


class _LastAPI:
    def __init__(self, use_case: LastUseCase, scope: Scope):
        self._uc = use_case
        self._scope = scope

    async def get(self) -> Optional[Dict[str, Any]]:
        jlog(logger, logging.INFO, LogCode.NAVIGATOR_API, method="last.get", scope=scope_kv(self._scope))
        async with locks.guard(self._scope):
            mid = await self._uc.get_id()
        if mid is None:
            return None
        return {
            "id": mid,
            "inline": bool(self._scope.inline_id),
            "chat": self._scope.chat,
        }

    async def delete(self) -> None:
        jlog(logger, logging.INFO, LogCode.NAVIGATOR_API, method="last.delete", scope=scope_kv(self._scope))
        async with locks.guard(self._scope):
            await self._uc.delete(self._scope)

    async def edit(self, content: Content) -> Optional[int]:
        jlog(
            logger,
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="last.edit",
            scope=scope_kv(self._scope),
            payload={"text": bool(content.text), "media": bool(content.media), "group": bool(content.group)},
        )
        async with locks.guard(self._scope):
            result = await self._uc.edit(self._scope, to_payload(content))
        return result


class Navigator:
    def __init__(
            self,
            *,
            add_uc: AddUseCase,
            replace_uc: ReplaceUseCase,
            back_uc: BackUseCase,
            set_uc: SetUseCase,
            pop_uc: PopUseCase,
            rebase_uc: RebaseUseCase,
            last_uc: LastUseCase,
            notify_history_empty_uc: NotifyHistoryEmptyUseCase,
            scope: Scope,
    ):
        self._add = add_uc
        self._replace = replace_uc
        self._back = back_uc
        self._set = set_uc
        self._pop = pop_uc
        self._rebase = rebase_uc
        self._notify_history_empty = notify_history_empty_uc
        self._scope = scope
        self.last = _LastAPI(use_case=last_uc, scope=scope)

    async def add(self, content: Union[Content, Node], *, key: Optional[str] = None, root: bool = False) -> None:
        node = content if isinstance(content, Node) else Node(messages=[content])
        payloads = to_node_payload(node)
        jlog(
            logger,
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="add",
            scope=scope_kv(self._scope),
            key=key,
            root=root,
            payload={"count": len(payloads)},
        )
        async with locks.guard(self._scope):
            await self._add.execute(self._scope, payloads, key, root=root)

    async def replace(self, content: Union[Content, Node]) -> None:
        node = content if isinstance(content, Node) else Node(messages=[content])
        payloads = to_node_payload(node)
        jlog(
            logger,
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="replace",
            scope=scope_kv(self._scope),
            payload={"count": len(payloads)},
        )
        async with locks.guard(self._scope):
            await self._replace.execute(self._scope, payloads)

    async def rebase(self, message: int | SupportsInt) -> None:
        mid = getattr(message, "id", message)
        jlog(
            logger,
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="rebase",
            scope=scope_kv(self._scope),
            message={"id": int(mid)},
        )
        async with locks.guard(self._scope):
            await self._rebase.execute(int(mid))

    async def back(self, handler_data: Dict[str, Any]) -> None:
        jlog(
            logger,
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method="back",
            scope=scope_kv(self._scope),
            handler_keys=sorted(list(handler_data.keys())) if isinstance(handler_data, dict) else None,
        )
        async with locks.guard(self._scope):
            await self._back.execute(self._scope, handler_data)

    async def set(self, state: Union[str, StateLike], handler_data: Dict[str, Any] | None = None) -> None:
        st = getattr(state, "state", state)
        jlog(logger, logging.INFO, LogCode.NAVIGATOR_API, method="set", scope=scope_kv(self._scope), state=st)
        async with locks.guard(self._scope):
            await self._set.execute(self._scope, st, handler_data or {})

    async def pop(self, count: int = 1) -> None:
        jlog(logger, logging.INFO, LogCode.NAVIGATOR_API, method="pop", scope=scope_kv(self._scope), count=count)
        async with locks.guard(self._scope):
            await self._pop.execute(count)

    async def inform_history_is_empty(self) -> None:
        jlog(logger, logging.INFO, LogCode.NAVIGATOR_API, method="notify_empty", scope=scope_kv(self._scope))
        async with locks.guard(self._scope):
            await self._notify_history_empty.execute(self._scope)

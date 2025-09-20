from __future__ import annotations

import asyncio
import logging
import os
from typing import List

from .retry import call_tg
from ..errors import any_soft_ignorable_exc
from ....domain.log.emit import jlog
from ....domain.service.scope import scope_kv
from ....domain.value.ids import unique_sorted as _uniq
from ....domain.value.message import Scope
from ....logging.code import LogCode

logger = logging.getLogger(__name__)
_DELAY_SEC = max(0.0, float(int(os.getenv("NAV_DELETE_DELAY_MS", "50"))) / 1000.0)


class BatchDeleteRunner:
    def __init__(self, bot, chunk_size: int):
        self._bot = bot
        self._chunk = min(int(chunk_size), 100)

    async def run(self, scope: Scope, ids: List[int]) -> None:
        if scope.inline_id and not scope.biz_id:
            jlog(
                logger,
                logging.INFO,
                LogCode.RENDER_SKIP,
                scope=scope_kv(scope),
                note="inline_without_biz_delete_skip",
                count=len(ids or []),
            )
            return
        if not ids:
            return
        uniq_ids = _uniq(ids)
        if not uniq_ids:
            return
        parts = [uniq_ids[i:i + self._chunk] for i in range(0, len(uniq_ids), self._chunk)]
        total = len(parts)
        jlog(
            logger,
            logging.DEBUG,
            LogCode.RERENDER_START,
            note="delete_chunking",
            count=len(uniq_ids),
            chunks=total,
            chunk_size=self._chunk,
        )
        try:
            for idx, part in enumerate(parts, start=1):
                try:
                    if scope.biz_id:
                        try:
                            await call_tg(
                                self._bot.delete_business_messages,
                                business_connection_id=scope.biz_id,
                                message_ids=part,
                            )
                            jlog(
                                logger,
                                logging.INFO,
                                LogCode.GATEWAY_DELETE_OK,
                                scope=scope_kv(scope),
                                message={"deleted": len(part)},
                                chunk={"index": idx, "total": total},
                            )
                            await asyncio.sleep(_DELAY_SEC)
                        except Exception:
                            # Фоллбэк на обычное удаление
                            try:
                                await call_tg(
                                    self._bot.delete_messages,
                                    chat_id=scope.chat,
                                    message_ids=part,
                                )
                                jlog(
                                    logger,
                                    logging.INFO,
                                    LogCode.GATEWAY_DELETE_OK,
                                    scope=scope_kv(scope),
                                    message={"deleted": len(part)},
                                    chunk={"index": idx, "total": total},
                                )
                                await asyncio.sleep(_DELAY_SEC)
                            except Exception as e_fallback:
                                if any_soft_ignorable_exc(e_fallback):
                                    continue
                                raise
                    else:
                        await call_tg(
                            self._bot.delete_messages,
                            chat_id=scope.chat,
                            message_ids=part,
                        )
                        jlog(
                            logger,
                            logging.INFO,
                            LogCode.GATEWAY_DELETE_OK,
                            scope=scope_kv(scope),
                            message={"deleted": len(part)},
                            chunk={"index": idx, "total": total},
                        )
                        await asyncio.sleep(_DELAY_SEC)
                except Exception as e:
                    if any_soft_ignorable_exc(e):
                        continue
                    raise
        except Exception as e:
            jlog(
                logger,
                logging.WARNING,
                LogCode.GATEWAY_DELETE_FAIL,
                scope=scope_kv(scope),
                count=len(uniq_ids),
                note=type(e).__name__,
            )
            raise

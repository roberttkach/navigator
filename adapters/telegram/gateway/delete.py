from __future__ import annotations

import asyncio
import logging
import os
from typing import List

from .retry import invoke
from ..errors import excusable
from ....domain.log.emit import jlog
from ....domain.service.scope import profile
from ....domain.value.ids import order as _order
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)
_DELAY_SEC = max(0.0, float(int(os.getenv("NAV_DELETE_DELAY_MS", "50"))) / 1000.0)


class DeleteBatch:
    def __init__(self, bot, chunk: int):
        self._bot = bot
        self._chunk = min(int(chunk), 100)

    async def run(self, scope: Scope, identifiers: List[int]) -> None:
        if scope.inline and not scope.business:
            jlog(
                logger,
                logging.INFO,
                LogCode.RENDER_SKIP,
                scope=profile(scope),
                note="inline_without_business_delete_skip",
                count=len(identifiers or []),
            )
            return
        if not identifiers:
            return
        unique = _order(identifiers)
        if not unique:
            return
        groups = [
            unique[start:start + self._chunk]
            for start in range(0, len(unique), self._chunk)
        ]
        total = len(groups)
        jlog(
            logger,
            logging.DEBUG,
            LogCode.RERENDER_START,
            note="delete_chunking",
            count=len(unique),
            chunks=total,
            chunk=self._chunk,
        )
        try:
            for index, group in enumerate(groups, start=1):
                try:
                    if scope.business:
                        try:
                            await invoke(
                                self._bot.delete_business_messages,
                                business_connection_id=scope.business,
                                message_ids=group,
                            )
                            jlog(
                                logger,
                                logging.INFO,
                                LogCode.GATEWAY_DELETE_OK,
                                scope=profile(scope),
                                message={"deleted": len(group)},
                                chunk={"index": index, "total": total},
                            )
                            await asyncio.sleep(_DELAY_SEC)
                        except Exception:
                            try:
                                await invoke(
                                    self._bot.delete_messages,
                                    chat_id=scope.chat,
                                    message_ids=group,
                                )
                                jlog(
                                    logger,
                                    logging.INFO,
                                    LogCode.GATEWAY_DELETE_OK,
                                    scope=profile(scope),
                                    message={"deleted": len(group)},
                                    chunk={"index": index, "total": total},
                                )
                                await asyncio.sleep(_DELAY_SEC)
                            except Exception as fallback:
                                if excusable(fallback):
                                    continue
                                raise
                    else:
                        await invoke(
                            self._bot.delete_messages,
                            chat_id=scope.chat,
                            message_ids=group,
                        )
                        jlog(
                            logger,
                            logging.INFO,
                            LogCode.GATEWAY_DELETE_OK,
                            scope=profile(scope),
                            message={"deleted": len(group)},
                            chunk={"index": index, "total": total},
                        )
                        await asyncio.sleep(_DELAY_SEC)
                except Exception as error:
                    if excusable(error):
                        continue
                    raise
        except Exception as error:
            jlog(
                logger,
                logging.WARNING,
                LogCode.GATEWAY_DELETE_FAIL,
                scope=profile(scope),
                count=len(unique),
                note=type(error).__name__,
            )
            raise

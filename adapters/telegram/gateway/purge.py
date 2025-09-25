from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Optional

from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.ids import order as arrange
from navigator.core.value.message import Scope

from .retry import invoke
from ..errors import excusable


class PurgeTask:
    """Coordinate Telegram message purge operations."""

    def __init__(self, bot, *, chunk: int, delay: float, telemetry: Telemetry) -> None:
        self._bot = bot
        size = int(chunk)
        self._chunk = max(min(size, 100), 1)
        self._delay = max(float(delay), 0.0)
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def execute(self, scope: Scope, identifiers: Sequence[int]) -> None:
        """Dispatch deletion requests in safe, chunked batches."""

        if self._should_skip(scope, identifiers):
            return

        unique = arrange(identifiers)
        batches = self._chunked(unique)
        if not batches:
            return

        count = len(unique)
        purger, params = self._resolve_purger(scope)
        await self._purge_batches(scope, batches, purger, params, count)

    def _should_skip(self, scope: Scope, identifiers: Sequence[int]) -> bool:
        """Report whether inline context forbids purge calls."""

        if scope.inline and not scope.business:
            self._channel.emit(
                logging.INFO,
                LogCode.RENDER_SKIP,
                scope=profile(scope),
                note="inline_without_business_delete_skip",
                count=len(identifiers),
            )
            return True
        return False

    def _chunked(self, identifiers: Sequence[int]) -> list[list[int]]:
        """Group identifiers into fixed-size batches for deletion."""

        if not identifiers:
            return []
        unique = list(identifiers)
        return [
            unique[start:start + self._chunk]
            for start in range(0, len(unique), self._chunk)
        ]

    def _resolve_purger(
            self,
            scope: Scope,
    ) -> tuple[Optional[Callable[..., Awaitable[Any]]], dict[str, Any]]:
        if scope.business:
            purger = getattr(self._bot, "delete_business_messages", None)
            params = {"business_connection_id": scope.business}
        else:
            purger = getattr(self._bot, "delete_messages", None)
            params = {"chat_id": scope.chat}
        return purger, params

    async def _purge_batches(
            self,
            scope: Scope,
            batches: Sequence[Sequence[int]],
            purger: Optional[Callable[..., Awaitable[Any]]],
            params: dict[str, Any],
            count: int,
    ) -> None:
        """Apply purge batches while streaming telemetry events."""

        total = len(batches)
        self._channel.emit(
            logging.DEBUG,
            LogCode.RERENDER_START,
            note="delete_chunking",
            count=count,
            chunks=total,
            chunk=self._chunk,
        )
        scopeview = profile(scope)
        try:
            for index, batch in enumerate(batches, start=1):
                try:
                    await self._execute_batch(scope, batch, purger, params)
                except Exception as error:
                    if excusable(error):
                        continue
                    raise
                self._channel.emit(
                    logging.INFO,
                    LogCode.GATEWAY_DELETE_OK,
                    scope=scopeview,
                    message={"deleted": len(batch)},
                    chunk={"index": index, "total": total},
                )
                if self._delay:
                    await asyncio.sleep(self._delay)
        except Exception as error:
            self._channel.emit(
                logging.WARNING,
                LogCode.GATEWAY_DELETE_FAIL,
                scope=scopeview,
                count=count,
                note=type(error).__name__,
            )
            raise

    async def _execute_batch(
            self,
            scope: Scope,
            batch: Sequence[int],
            purger: Optional[Callable[..., Awaitable[Any]]],
            params: dict[str, Any],
    ) -> None:
        """Perform a single purge batch call respecting business rules."""

        if purger is not None:
            await invoke(
                purger,
                message_ids=batch,
                **params,
                channel=self._channel,
            )
            return

        if scope.business:
            raise RuntimeError("bulk_business_delete_unsupported")

        for mid in batch:
            await invoke(
                self._bot.delete_message,
                chat_id=scope.chat,
                message_id=mid,
                channel=self._channel,
            )

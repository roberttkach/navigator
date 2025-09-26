"""Refresh and reconcile the leading album message if required."""

from __future__ import annotations

import logging

from navigator.core.entity.history import Message
from navigator.core.telemetry import LogCode, Telemetry
from navigator.core.telemetry import TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..album import AlbumService

from .models import RenderState


class HeadAlignment:
    """Refresh and reconcile the leading album message if required."""

    def __init__(self, album: AlbumService, telemetry: Telemetry) -> None:
        self._album = album
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.head")

    async def align(
        self,
        scope: Scope,
        ledger: list[Message],
        fresh: list[Payload],
        state: RenderState,
    ) -> tuple[int, bool]:
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


__all__ = ["HeadAlignment"]


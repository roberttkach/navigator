"""Persist conversation history with telemetry instrumentation."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import replace

from ...core.entity.history import Entry, Message
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload


def preserve(payload: Payload, entry: Message | None) -> Payload:
    """Return ``payload`` with preview and extra inherited from ``entry``."""

    if entry is None:
        return payload

    preview = _inherit(payload.preview, entry.preview)
    extra = _inherit(payload.extra, entry.extra)
    if preview is payload.preview and extra is payload.extra:
        return payload
    return replace(payload, preview=preview, extra=extra)


def _inherit(current: object | None, fallback: object | None) -> object | None:
    """Return ``current`` unless it is ``None``, falling back to ``fallback``."""

    return current if current is not None else fallback


def _channel_for(telemetry: Telemetry | None) -> TelemetryChannel | None:
    """Return a telemetry channel dedicated to storage operations."""

    return telemetry.channel(__name__) if telemetry else None


def _emit(
        channel: TelemetryChannel | None,
        level: int,
        code: LogCode,
        **payload: object,
) -> None:
    """Emit a telemetry envelope if ``channel`` is configured."""
    if channel is None:
        return
    channel.emit(level, code, **payload)


def _latest_marker(history: Sequence[Entry]) -> int | None:
    """Return the first message identifier for the most recent entry."""

    if not history:
        return None
    messages = history[-1].messages
    if not messages:
        return None
    return messages[0].id


async def persist(
        archive: HistoryRepository,
        ledger: LatestRepository,
        prune_history: Callable[[list[Entry], int], list[Entry]],
        limit: int,
        history: Sequence[Entry],
        *,
        operation: str,
        telemetry: Telemetry | None = None,
) -> None:
    """Persist the supplied ``history`` snapshot and update ``ledger``."""

    channel = _channel_for(telemetry)
    snapshot = list(history)
    trimmed = prune_history(snapshot, limit)
    if len(trimmed) != len(snapshot):
        _emit(
            channel,
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=operation,
            history={"before": len(snapshot), "after": len(trimmed)},
        )

    await archive.archive(trimmed)
    _emit(
        channel,
        logging.DEBUG,
        LogCode.HISTORY_SAVE,
        op=operation,
        history={"len": len(trimmed)},
    )

    marker = _latest_marker(trimmed)
    if marker is None:
        return

    await ledger.mark(marker)
    _emit(
        channel,
        logging.INFO,
        LogCode.LAST_SET,
        op=operation,
        message={"id": marker},
    )

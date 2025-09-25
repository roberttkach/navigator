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
    """Keep payload preview and extra in sync with latest entry."""

    if entry is None:
        return payload

    preview = payload.preview if payload.preview is not None else entry.preview
    extra = payload.extra if payload.extra is not None else entry.extra
    if preview is payload.preview and extra is payload.extra:
        return payload
    return replace(payload, preview=preview, extra=extra)


def _emit(
        channel: TelemetryChannel | None,
        level: int,
        code: LogCode,
        **payload: object,
) -> None:
    if channel is None:
        return
    channel.emit(level, code, **payload)


def _latest_marker(history: Sequence[Entry]) -> int | None:
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
    """Persist updated history snapshots with telemetry support."""

    channel: TelemetryChannel | None = (
        telemetry.channel(__name__) if telemetry else None
    )
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


def reindex(
        entry: Entry,
        identifiers: Sequence[int],
        extras: Sequence[Sequence[int]] | None = None,
) -> Entry:
    """Rebuild entry messages with provided identifiers and extras."""

    limit = min(len(entry.messages), len(identifiers))
    if limit == 0:
        return entry

    updated: list[Message] = []
    for index in range(limit):
        message = entry.messages[index]
        provided = (
            list(extras[index])
            if extras is not None and index < len(extras)
            else message.extras
        )
        updated.append(
            replace(
                message,
                id=int(identifiers[index]),
                extras=provided,
            )
        )

    if limit < len(entry.messages):
        updated.extend(entry.messages[limit:])

    return replace(entry, messages=updated)

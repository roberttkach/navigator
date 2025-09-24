from __future__ import annotations

import logging
from dataclasses import replace
from typing import List, Optional

from ...core.entity.history import Entry, Message
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel


def preserve(payload, entry):
    return replace(
        payload,
        preview=payload.preview if payload.preview is not None else entry.preview,
        extra=payload.extra if payload.extra is not None else entry.extra,
    )


async def persist(
    archive,
    ledger,
    policy,
    limit,
    history,
    *,
    operation: str,
    telemetry: Telemetry | None = None,
):
    channel: TelemetryChannel | None = (
        telemetry.channel(__name__) if telemetry else None
    )
    trimmed = policy.prune(history, limit)
    if len(trimmed) != len(history) and channel is not None:
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=operation,
            history={"before": len(history), "after": len(trimmed)},
        )
    await archive.archive(trimmed)
    if channel is not None:
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op=operation,
            history={"len": len(trimmed)},
        )
    if trimmed and trimmed[-1].messages:
        marker = trimmed[-1].messages[0].id
        await ledger.mark(marker)
        if channel is not None:
            channel.emit(
                logging.INFO,
                LogCode.LAST_SET,
                op=operation,
                message={"id": marker},
            )


def reindex(entry: Entry, identifiers: List[int], extras: Optional[List[List[int]]] = None) -> Entry:
    limit = min(len(entry.messages), len(identifiers))
    messages: List[Message] = []
    for index in range(limit):
        messages.append(
            Message(
                id=int(identifiers[index]),
                text=entry.messages[index].text,
                media=entry.messages[index].media,
                group=entry.messages[index].group,
                markup=entry.messages[index].markup,
                preview=entry.messages[index].preview,
                extra=entry.messages[index].extra,
                extras=(extras[index] if extras and index < len(extras) else entry.messages[index].extras),
                inline=entry.messages[index].inline,
                automated=entry.messages[index].automated,
                ts=entry.messages[index].ts,
            )
        )
    messages += entry.messages[limit:]
    return Entry(state=entry.state, view=entry.view, messages=messages, root=entry.root)

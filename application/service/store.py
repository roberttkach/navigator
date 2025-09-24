from __future__ import annotations

import logging
from dataclasses import replace
from typing import List, Optional

from navigator.log import LogCode, jlog
from ...domain.entity.history import Entry, Message

logger = logging.getLogger(__name__)


def preserve(payload, entry):
    return replace(
        payload,
        preview=payload.preview if payload.preview is not None else entry.preview,
        extra=payload.extra if payload.extra is not None else entry.extra,
    )


async def persist(archive, ledger, policy, limit, history, *, operation: str):
    trimmed = policy.prune(history, limit)
    if len(trimmed) != len(history):
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=operation,
            history={"before": len(history), "after": len(trimmed)},
        )
    await archive.archive(trimmed)
    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op=operation, history={"len": len(trimmed)})
    if trimmed and trimmed[-1].messages:
        marker = trimmed[-1].messages[0].id
        await ledger.mark(marker)
        jlog(logger, logging.INFO, LogCode.LAST_SET, op=operation, message={"id": marker})


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

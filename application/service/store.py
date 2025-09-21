import logging
from dataclasses import replace
from typing import List, Optional

from ..log.emit import jlog
from ...domain.entity.history import Entry, Msg
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def preserve(payload, entry):
    return replace(
        payload,
        preview=payload.preview if payload.preview is not None else entry.preview,
        extra=payload.extra if payload.extra is not None else entry.extra,
    )


async def persist(archive, ledger, policy, limit, history, *, op: str):
    trimmed = policy.prune(history, limit)
    if len(trimmed) != len(history):
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=op,
            history={"before": len(history), "after": len(trimmed)},
        )
    await archive.archive(trimmed)
    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op=op, history={"len": len(trimmed)})
    if trimmed and trimmed[-1].messages:
        mid = trimmed[-1].messages[0].id
        await ledger.mark(mid)
        jlog(logger, logging.INFO, LogCode.LAST_SET, op=op, message={"id": mid})


def reindex(entry: Entry, ids: List[int], extras: Optional[List[List[int]]] = None) -> Entry:
    limit = min(len(entry.messages), len(ids))
    messages = []
    for i in range(limit):
        messages.append(
            Msg(
                id=int(ids[i]),
                text=entry.messages[i].text,
                media=entry.messages[i].media,
                group=entry.messages[i].group,
                markup=entry.messages[i].markup,
                preview=entry.messages[i].preview,
                extra=entry.messages[i].extra,
                extras=(extras[i] if extras and i < len(extras) else entry.messages[i].extras),
                inline=entry.messages[i].inline,
                automated=entry.messages[i].automated,
                ts=entry.messages[i].ts,
            )
        )
    messages += entry.messages[limit:]
    return Entry(state=entry.state, view=entry.view, messages=messages, root=entry.root)

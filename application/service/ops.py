import logging
from dataclasses import replace
from typing import List, Optional

from ..log.emit import jlog
from ...domain.entity.history import Entry, Msg
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def keep_preview_extra(p, e):
    return replace(
        p,
        preview=p.preview if p.preview is not None else e.preview,
        extra=p.extra if p.extra is not None else e.extra,
    )


async def save_history_and_last(history_repo, last_repo, history_policy, history_limit, new_history, *, op: str):
    trimmed = history_policy.prune(new_history, history_limit)
    if len(trimmed) != len(new_history):
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=op,
            history={"before": len(new_history), "after": len(trimmed)},
        )
    await history_repo.save_history(trimmed)
    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op=op, history={"len": len(trimmed)})
    if trimmed and trimmed[-1].messages:
        mid = trimmed[-1].messages[0].id
        await last_repo.set_last_id(mid)
        jlog(logger, logging.INFO, LogCode.LAST_SET, op=op, message={"id": mid})


def patch_entry_ids(entry: Entry, new_ids: List[int], new_extras: Optional[List[List[int]]] = None) -> Entry:
    limit = min(len(entry.messages), len(new_ids))
    patched_msgs = []
    for i in range(limit):
        patched_msgs.append(
            Msg(
                id=int(new_ids[i]),
                text=entry.messages[i].text,
                media=entry.messages[i].media,
                group=entry.messages[i].group,
                markup=entry.messages[i].markup,
                preview=entry.messages[i].preview,
                extra=entry.messages[i].extra,
                extras=(new_extras[i] if new_extras and i < len(new_extras) else entry.messages[i].extras),
                inline_id=entry.messages[i].inline_id,
                automated=entry.messages[i].automated,
                ts=entry.messages[i].ts,
            )
        )
    patched_msgs += entry.messages[limit:]
    return Entry(state=entry.state, view=entry.view, messages=patched_msgs, root=entry.root)

import inspect
import logging
from html import escape
from typing import Optional, Dict, Any, List

from ...log.emit import jlog
from ....domain.entity.history import Entry
from ....domain.port.factory import ViewLedger
from ....domain.value.content import Payload
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


class ViewRestorer:
    def __init__(self, ledger: ViewLedger):
        self._ledger = ledger

    async def revive(self, entry: Entry, context: Dict[str, Any], *, inline: bool) -> List[Payload]:
        if entry.view:
            jlog(logger, logging.INFO, LogCode.RESTORE_DYNAMIC, forge=entry.view)
            content = await self._dynamic(entry.view, context)
            if content:
                if isinstance(content, list):
                    if inline and len(content) > 1:
                        jlog(
                            logger,
                            logging.WARNING,
                            LogCode.RESTORE_DYNAMIC_FALLBACK,
                            forge=entry.view,
                            note="inline_multi_payload_trimmed",
                            count=len(content),
                        )
                        return [content[0]]
                    return content
                return [content]
        return [self._static(m) for m in entry.messages]

    async def _dynamic(
            self, key: str, context: Dict[str, Any]
    ) -> Optional[Payload | List[Payload]]:
        try:
            forge = self._ledger.get(key)
        except KeyError:
            jlog(logger, logging.WARNING, LogCode.RESTORE_DYNAMIC_FALLBACK, forge=key, note="factory_not_found")
            return None
        try:
            params = inspect.signature(forge).parameters
            supplies = {name: context[name] for name in params if name in context}
            content = await forge(**supplies)
            return content
        except Exception as e:
            jlog(
                logger,
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note=type(e).__name__,
                exc_info=True,
                error={"type": type(e).__name__},
            )
            return None

    @staticmethod
    def _static(m) -> Payload:
        text = getattr(m, "text", None)

        if text is None and getattr(m, "media", None):
            cap = getattr(m.media, "caption", None)
            if isinstance(cap, str) and cap:
                text = escape(cap)

        return Payload(
            text=text,
            media=m.media,
            group=m.group,
            reply=m.markup,
            preview=m.preview,
            extra=m.extra,
        )

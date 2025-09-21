import inspect
import logging
from html import escape
from typing import Optional, Dict, Any, List

from ...log.emit import jlog
from ....domain.entity.history import Entry
from ....domain.port.factory import ViewFactoryRegistry
from ....domain.port.markup import MarkupCodec
from ....domain.value.content import Payload
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


class ViewRestorer:
    def __init__(self, markup_codec: MarkupCodec, factory_registry: ViewFactoryRegistry):
        self._markup_codec = markup_codec
        self._factory_registry = factory_registry

    async def restore_node(self, entry: Entry, context: Dict[str, Any], *, inline: bool) -> List[Payload]:
        if entry.view:
            jlog(logger, logging.INFO, LogCode.RESTORE_DYNAMIC, factory_key=entry.view)
            content = await self._try_dynamic_restore(entry.view, context)
            if content:
                if isinstance(content, list):
                    if inline and len(content) > 1:
                        jlog(
                            logger,
                            logging.WARNING,
                            LogCode.RESTORE_DYNAMIC_FALLBACK,
                            factory_key=entry.view,
                            note="inline_multi_payload_trimmed",
                            count=len(content),
                        )
                        return [content[0]]
                    return content
                return [content]
        return [self._static_restore_msg(m) for m in entry.messages]

    async def restore(self, entry: Entry, context: Dict[str, Any], *, inline: bool = False) -> Payload:
        res = await self.restore_node(entry, context, inline=inline)
        return res[0] if res else Payload()

    async def _try_dynamic_restore(
            self, key: str, context: Dict[str, Any]
    ) -> Optional[Payload | List[Payload]]:
        try:
            factory = self._factory_registry.get(key)
        except KeyError:
            jlog(logger, logging.WARNING, LogCode.RESTORE_DYNAMIC_FALLBACK, factory_key=key, note="factory_not_found")
            return None
        try:
            factory_params = inspect.signature(factory).parameters
            supplies = {name: context[name] for name in factory_params if name in context}
            content = await factory(**supplies)
            return content
        except Exception as e:
            jlog(
                logger,
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                factory_key=key,
                note=type(e).__name__,
                exc_info=True,
                error={"type": type(e).__name__},
            )
            return None

    @staticmethod
    def _static_restore_msg(m) -> Payload:
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

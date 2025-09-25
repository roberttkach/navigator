from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, List, Optional

from ....core.entity.history import Entry
from ....core.error import InlineUnsupported
from ....core.port.factory import ViewLedger
from ....core.telemetry import LogCode, Telemetry, TelemetryChannel
from ....core.value.content import Payload


class ViewRestorer:
    def __init__(self, ledger: ViewLedger, telemetry: Telemetry):
        self._ledger = ledger
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def revive(self, entry: Entry, context: Dict[str, Any], *, inline: bool) -> List[Payload]:
        if entry.view:
            self._channel.emit(logging.INFO, LogCode.RESTORE_DYNAMIC, forge=entry.view)
            content = await self._dynamic(entry.view, context)
            if content:
                if isinstance(content, list):
                    if inline and len(content) > 1:
                        raise InlineUnsupported("inline_dynamic_multi_payload")
                    return content
                return [content]
        return [self._static(m) for m in entry.messages]

    async def _dynamic(
            self,
            key: str,
            context: Dict[str, Any],
    ) -> Optional[Payload | List[Payload]]:
        try:
            forge = self._ledger.get(key)
        except KeyError:
            self._channel.emit(
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note="factory_not_found",
            )
            return None
        try:
            params = inspect.signature(forge).parameters
            supplies = {name: context[name] for name in params if name in context}
            content = await forge(**supplies)
            return content
        except Exception as exc:
            self._channel.emit(
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note=type(exc).__name__,
                exc_info=True,
                error={"type": type(exc).__name__},
            )
            return None

    @staticmethod
    def _static(message) -> Payload:
        text = getattr(message, "text", None)
        media = getattr(message, "media", None)

        if text is None and media is not None:
            caption = getattr(media, "caption", None)
            if isinstance(caption, str) and caption:
                text = caption

        return Payload(
            text=text,
            media=media,
            group=message.group,
            reply=message.markup,
            preview=message.preview,
            extra=message.extra,
        )

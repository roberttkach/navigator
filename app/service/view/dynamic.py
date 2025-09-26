"""Dynamic view restoration workflow."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, List, Optional

from ....core.entity.history import Entry
from ....core.error import InlineUnsupported
from ....core.port.factory import ViewLedger
from ....core.telemetry import LogCode, TelemetryChannel
from ....core.value.content import Payload

from .forge import ForgeInvoker, ForgeResolver


class DynamicPayloadNormaliser:
    """Ensure dynamic payload output respects inline constraints."""

    def normalize(
        self,
        content: Optional[Payload | List[Payload]],
        *,
        inline: bool,
    ) -> Optional[List[Payload]]:
        if not content:
            return None
        if isinstance(content, list):
            if inline and len(content) > 1:
                raise InlineUnsupported("inline_dynamic_multi_payload")
            return content
        return [content]


class DynamicViewRestorer:
    """Coordinate the dynamic restoration pipeline."""

    def __init__(
        self,
        *,
        channel: TelemetryChannel,
        ledger: ViewLedger,
        resolver: ForgeResolver | None = None,
        invoker: ForgeInvoker | None = None,
        normaliser: DynamicPayloadNormaliser | None = None,
    ) -> None:
        self._channel = channel
        self._resolver = resolver or ForgeResolver(ledger, channel)
        self._invoker = invoker or ForgeInvoker(channel)
        self._normaliser = normaliser or DynamicPayloadNormaliser()

    async def restore(
        self,
        entry: Entry,
        context: Mapping[str, Any],
        *,
        inline: bool,
    ) -> Optional[List[Payload]]:
        if not entry.view:
            return None

        self._channel.emit(logging.INFO, LogCode.RESTORE_DYNAMIC, forge=entry.view)
        forge = self._resolver.resolve(entry.view)
        if forge is None:
            return None
        content = await self._invoker.invoke(entry.view, forge, context)
        return self._normaliser.normalize(content, inline=inline)


__all__ = [
    "DynamicPayloadNormaliser",
    "DynamicViewRestorer",
]

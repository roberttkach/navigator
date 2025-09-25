"""Restore view payloads via ledger-backed factories."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Dict, List, Optional

from ....core.entity.history import Entry, Message
from ....core.error import InlineUnsupported
from ....core.port.factory import ViewLedger
from ....core.telemetry import LogCode, Telemetry, TelemetryChannel
from ....core.value.content import Payload

_Forge = Callable[..., Awaitable[Optional[Payload | List[Payload]]]]


class ViewRestorer:
    """Orchestrate static and dynamic view restoration."""

    def __init__(self, ledger: ViewLedger, telemetry: Telemetry):
        self._ledger = ledger
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def revive(
            self,
            entry: Entry,
            context: Dict[str, Any],
            *,
            inline: bool,
    ) -> List[Payload]:
        """Return payloads for ``entry`` while respecting inline rules."""

        if entry.view:
            self._channel.emit(logging.INFO, LogCode.RESTORE_DYNAMIC, forge=entry.view)
            content = await self._resolve_dynamic(entry.view, context)
            payloads = self._coerce_payloads(content, inline)
            if payloads is not None:
                return payloads

        return [self._static(message) for message in entry.messages]

    async def _resolve_dynamic(
            self,
            key: str,
            context: Mapping[str, Any],
    ) -> Optional[Payload | List[Payload]]:
        forge = self._obtain_forge(key)
        if forge is None:
            return None
        return await self._invoke_forge(key, forge, context)

    def _obtain_forge(self, key: str) -> Optional[_Forge]:
        try:
            return self._ledger.get(key)
        except KeyError:
            self._channel.emit(
                logging.WARNING,
                LogCode.RESTORE_DYNAMIC_FALLBACK,
                forge=key,
                note="factory_not_found",
            )
            return None

    async def _invoke_forge(
            self,
            key: str,
            forge: _Forge,
            context: Mapping[str, Any],
    ) -> Optional[Payload | List[Payload]]:
        try:
            supplies = self._extract_supplies(forge, context)
            return await forge(**supplies)
        except Exception as exc:  # pragma: no cover - defensive
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
    def _extract_supplies(
            forge: _Forge,
            context: Mapping[str, Any],
    ) -> Dict[str, Any]:
        parameters = inspect.signature(forge).parameters
        return {name: context[name] for name in parameters if name in context}

    def _coerce_payloads(
            self,
            content: Optional[Payload | List[Payload]],
            inline: bool,
    ) -> Optional[List[Payload]]:
        if not content:
            return None
        if isinstance(content, list):
            if inline and len(content) > 1:
                raise InlineUnsupported("inline_dynamic_multi_payload")
            return content
        return [content]

    @staticmethod
    def _static(message: Message) -> Payload:
        """Convert a stored message into a payload shell."""

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

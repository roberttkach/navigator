"""Describe dynamic and static view restoration workflows."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from typing import Any, Dict, List, Optional, Tuple

from ....core.entity.history import Entry, Message
from ....core.error import InlineUnsupported
from ....core.port.factory import ViewLedger
from ....core.telemetry import LogCode, Telemetry, TelemetryChannel
from ....core.value.content import Payload

_Forge = Callable[..., Awaitable[Optional[Payload | List[Payload]]]]
_SUPPLIES_ATTR = "__navigator_supplies__"


def forge_supplies(*names: str) -> Callable[[_Forge], _Forge]:
    """Annotate ``forge`` with the context keys it expects."""

    required = _normalize_supplies(names)

    def decorator(forge: _Forge) -> _Forge:
        setattr(forge, _SUPPLIES_ATTR, required)
        return forge

    return decorator


def _normalize_supplies(names: Iterable[str]) -> Tuple[str, ...]:
    """Return stable, de-duplicated supply names."""

    unique: Dict[str, None] = {}
    for name in names:
        unique[str(name)] = None
    return tuple(unique.keys())


def _declared_supplies(forge: _Forge) -> Tuple[str, ...]:
    """Fetch the supply declaration attached to ``forge`` if present."""

    declared = getattr(forge, _SUPPLIES_ATTR, ())
    if isinstance(declared, str):
        return (declared,)
    if isinstance(declared, Iterable):
        return _normalize_supplies(declared)
    return ()


class StaticPayloadFactory:
    """Transform stored messages into payload shells."""

    def build_many(self, messages: Sequence[Message]) -> List[Payload]:
        return [self.build(message) for message in messages]

    def build(self, message: Message) -> Payload:
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


class ForgeResolver:
    """Resolve view forges from the configured ledger."""

    def __init__(self, ledger: ViewLedger, channel: TelemetryChannel) -> None:
        self._ledger = ledger
        self._channel = channel

    def resolve(self, key: str) -> Optional[_Forge]:
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


class ForgeSuppliesExtractor:
    """Derive forge arguments from the provided context mapping."""

    def extract(self, forge: _Forge, context: Mapping[str, Any]) -> Dict[str, Any]:
        required = _declared_supplies(forge)
        if not required:
            return {}
        supplies: Dict[str, Any] = {}
        missing: list[str] = []
        for name in required:
            if name in context:
                supplies[name] = context[name]
            else:
                missing.append(name)
        if missing:
            raise KeyError(f"missing_supplies:{','.join(sorted(missing))}")
        return supplies


class ForgeInvoker:
    """Invoke dynamic forges while reporting telemetry on failures."""

    def __init__(
        self,
        channel: TelemetryChannel,
        extractor: ForgeSuppliesExtractor | None = None,
    ) -> None:
        self._channel = channel
        self._extractor = extractor or ForgeSuppliesExtractor()

    async def invoke(
        self,
        key: str,
        forge: _Forge,
        context: Mapping[str, Any],
    ) -> Optional[Payload | List[Payload]]:
        try:
            supplies = self._extractor.extract(forge, context)
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


class ViewRestorer:
    """Orchestrate static and dynamic view restoration."""

    def __init__(
        self,
        ledger: ViewLedger,
        telemetry: Telemetry,
        *,
        dynamic: DynamicViewRestorer | None = None,
        static_factory: StaticPayloadFactory | None = None,
    ) -> None:
        channel: TelemetryChannel = telemetry.channel(__name__)
        self._dynamic = dynamic or DynamicViewRestorer(channel=channel, ledger=ledger)
        self._static = static_factory or StaticPayloadFactory()

    async def revive(
        self,
        entry: Entry,
        context: Dict[str, Any],
        *,
        inline: bool,
    ) -> List[Payload]:
        """Return payloads for ``entry`` while respecting inline rules."""

        dynamic = await self._dynamic.restore(entry, context, inline=inline)
        if dynamic is not None:
            return dynamic
        return self._static.build_many(entry.messages)

"""Dynamic view restoration workflow."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
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
        resolver: ForgeResolver,
        invoker: ForgeInvoker,
        normaliser: DynamicPayloadNormaliser,
    ) -> None:
        self._channel = channel
        self._resolver = resolver
        self._invoker = invoker
        self._normaliser = normaliser

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


@dataclass(slots=True)
class DynamicRestorationFactory:
    """Create :class:`DynamicViewRestorer` instances from loosely coupled hooks."""

    channel: TelemetryChannel
    resolver_factory: Callable[[], ForgeResolver]
    invoker_factory: Callable[[], ForgeInvoker]
    normaliser_factory: Callable[[], DynamicPayloadNormaliser] = (
        DynamicPayloadNormaliser
    )

    def create(
        self,
        *,
        resolver: ForgeResolver | None = None,
        invoker: ForgeInvoker | None = None,
        normaliser: DynamicPayloadNormaliser | None = None,
    ) -> DynamicViewRestorer:
        return DynamicViewRestorer(
            channel=self.channel,
            resolver=resolver or self.resolver_factory(),
            invoker=invoker or self.invoker_factory(),
            normaliser=normaliser or self.normaliser_factory(),
        )


def create_dynamic_view_restorer(
    ledger: ViewLedger,
    channel: TelemetryChannel,
    *,
    resolver_factory: Callable[[ViewLedger, TelemetryChannel], ForgeResolver] | None = None,
    invoker_factory: Callable[[TelemetryChannel], ForgeInvoker] | None = None,
    normaliser_factory: Callable[[], DynamicPayloadNormaliser] | None = None,
) -> DynamicViewRestorer:
    """Convenience helper wiring default resolver, invoker and normaliser."""

    resolver_builder = resolver_factory or (lambda src, chan: ForgeResolver(src, chan))
    invoker_builder = invoker_factory or (lambda chan: ForgeInvoker(chan))
    factory = DynamicRestorationFactory(
        channel=channel,
        resolver_factory=lambda: resolver_builder(ledger, channel),
        invoker_factory=lambda: invoker_builder(channel),
        normaliser_factory=normaliser_factory or DynamicPayloadNormaliser,
    )
    return factory.create()


__all__ = [
    "DynamicPayloadNormaliser",
    "DynamicRestorationFactory",
    "DynamicViewRestorer",
    "create_dynamic_view_restorer",
]

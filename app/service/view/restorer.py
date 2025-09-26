"""Describe dynamic and static view restoration workflows."""

from __future__ import annotations

from typing import Any, Dict, List

from ....core.entity.history import Entry
from ....core.port.factory import ViewLedger
from ....core.telemetry import Telemetry, TelemetryChannel
from ....core.value.content import Payload

from .dynamic import (
    DynamicPayloadNormaliser,
    DynamicViewRestorer,
    create_dynamic_view_restorer,
)
from .forge import ForgeInvoker, ForgeResolver, ForgeSuppliesExtractor, forge_supplies
from .static import StaticPayloadFactory


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
        self._dynamic = dynamic or create_dynamic_view_restorer(ledger, channel)
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


__all__ = [
    "DynamicViewRestorer",
    "DynamicPayloadNormaliser",
    "ForgeInvoker",
    "ForgeResolver",
    "ForgeSuppliesExtractor",
    "StaticPayloadFactory",
    "ViewRestorer",
    "forge_supplies",
]

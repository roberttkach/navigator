from __future__ import annotations

from typing import Any, TYPE_CHECKING

from navigator.core.port.factory import ViewLedger
from navigator.presentation.telegram.assembly import (
    TelegramNavigatorAssembler,
    TelegramRuntimeConfiguration,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from navigator.presentation.navigator import Navigator


async def assemble(event: Any, state: Any, ledger: ViewLedger) -> "Navigator":
    assembler = TelegramNavigatorAssembler.create(
        ledger, configuration=TelegramRuntimeConfiguration.create()
    )
    return await assembler.assemble(event, state)


__all__ = ["assemble"]

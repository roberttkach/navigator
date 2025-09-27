"""Aiogram middleware that injects a Navigator instance into handler context."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Awaitable, Callable, Dict, Optional, Protocol, runtime_checkable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from navigator.api.contracts import NavigatorRuntimeInstrument
from navigator.core.port.factory import ViewLedger
from .assembly import (
    NavigatorAssembler,
    TelegramNavigatorAssembler,
    TelegramRuntimeConfiguration,
)

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


@runtime_checkable
class NavigatorState(Protocol):
    """Subset of FSM context behaviour required by the navigator."""

    async def get_state(self) -> Optional[str]: ...

    async def set_state(self, state: Optional[str]) -> None: ...

    async def get_data(self) -> Dict[str, Any]: ...

    async def update_data(self, data: Dict[str, Any]) -> Dict[str, Any]: ...


class NavigatorMiddleware(BaseMiddleware):
    """Construct and attach Navigator facades for every incoming event."""

    def __init__(self, assembler: NavigatorAssembler) -> None:
        self._assembler = assembler

    @classmethod
    def from_ledger(
        cls,
        ledger: ViewLedger,
        *,
        instrumentation: Iterable[NavigatorRuntimeInstrument] | None = None,
    ) -> "NavigatorMiddleware":
        """Provide a convenient constructor for the default assembler."""

        configuration = TelegramRuntimeConfiguration.create(
            instrumentation=instrumentation
        )
        return cls(
            TelegramNavigatorAssembler(ledger, configuration=configuration)
        )

    async def __call__(
            self,
            handler: Handler,
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if not isinstance(state, NavigatorState):  # pragma: no cover - runtime guard
            raise RuntimeError(
                "State context implementation is required to assemble Navigator"
            )
        navigator = await self._assembler.assemble(event, state)
        data["navigator"] = navigator
        return await handler(event, data)


__all__ = ["NavigatorMiddleware", "Handler"]

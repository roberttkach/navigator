from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery

from navigator.bootstrap.navigator import NavigatorRuntimeBundle
from navigator.presentation.alerts import lexeme
from navigator.presentation.telegram.back import (
    NavigatorBack,
    RetreatHandler,
    RetreatOutcome,
)

router = Router(name="navigator_handlers")

BACK_CALLBACK_DATA = "back"


def instrument(bundle: NavigatorRuntimeBundle) -> None:
    """Attach runtime helpers to the router data."""

    router.data["telemetry"] = bundle.telemetry
    router.data["retreat_handler"] = RetreatHandler(bundle.telemetry, lexeme)


def _handler() -> RetreatHandler:
    handler = router.data.get("retreat_handler")
    if isinstance(handler, RetreatHandler):
        return handler
    telemetry = router.data.get("telemetry")
    if telemetry is None:
        raise RuntimeError("Retreat handler requires telemetry instrumentation")
    generated = RetreatHandler(telemetry, lexeme)
    router.data["retreat_handler"] = generated
    return generated


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def retreat(cb: CallbackQuery, navigator: NavigatorBack, **data: dict[str, Any]) -> None:
    handler = _handler()
    outcome: RetreatOutcome = await handler(cb, navigator, data)
    await cb.answer(outcome.text, show_alert=outcome.show_alert)


__all__ = ["router", "NavigatorBack", "retreat", "BACK_CALLBACK_DATA", "instrument"]

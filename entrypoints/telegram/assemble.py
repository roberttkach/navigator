from __future__ import annotations

from typing import Any

from navigator.domain.port.factory import ViewLedger
from navigator.infrastructure.di.container import AppContainer
from navigator.log import calibrate
from navigator.presentation.alerts import prev_not_found
from navigator.presentation.bootstrap.navigator import build_navigator
from navigator.presentation.navigator import Navigator

from .scope import outline


async def assemble(event: Any, state: Any, ledger: ViewLedger) -> Navigator:
    container = AppContainer(event=event, state=state, ledger=ledger, alert=prev_not_found)
    settings = container.core().settings()
    calibrate(getattr(settings, "redaction", ""))
    scope = outline(event)
    return build_navigator(container, scope)


__all__ = ["assemble"]

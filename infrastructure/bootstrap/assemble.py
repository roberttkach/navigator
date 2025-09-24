from __future__ import annotations

from typing import Any

from navigator.domain.port.factory import ViewLedger as ViewLedgerProtocol
from navigator.infrastructure.config.settings import load as load_settings
from navigator.infrastructure.di.container import AppContainer
from navigator.logging import calibrate
from navigator.presentation.alerts import prev_not_found
from navigator.presentation.navigator import Navigator
from navigator.presentation.telegram.scope import outline as forge


async def assemble(event: Any, state: Any, ledger: ViewLedgerProtocol) -> Navigator:
    settings = load_settings()
    calibrate(settings.redaction)
    container = AppContainer(event=event, state=state, ledger=ledger, alert=prev_not_found)
    scope = forge(event)
    return Navigator(
        appender=container.appender(),
        swapper=container.swapper(),
        rewinder=container.rewinder(),
        setter=container.setter(),
        trimmer=container.trimmer(),
        shifter=container.shifter(),
        tailer=container.tailer(),
        alarm=container.alarm(),
        guard=container.guard(),
        scope=scope,
    )

from typing import Any

from ..application.log.emit import calibrate
from ..domain.port.factory import ViewLedger as ViewLedgerProtocol
from ..infrastructure.config import SETTINGS
from ..infrastructure.di.container import AppContainer
from ..infrastructure.locks import configure
from ..presentation.alerts import prev_not_found
from ..presentation.navigator import Navigator
from ..presentation.telegram.scope import outline as forge


async def assemble(event: Any, state: Any, ledger: ViewLedgerProtocol) -> Navigator:
    calibrate(SETTINGS.redaction)
    configure()
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
        scope=scope,
    )

from typing import Optional, Any

from ..adapters.factory.registry import default as fallback
from ..application.log.emit import calibrate
from ..infrastructure.config import SETTINGS
from ..infrastructure.di.container import AppContainer
from ..infrastructure.locks import configure
from ..presentation.navigator import Navigator
from ..presentation.telegram.scope import outline as forge


async def assemble(event: Any, state: Any, ledger: Optional[Any] = None) -> Navigator:
    calibrate(SETTINGS.redaction)
    configure()
    stock = ledger if ledger is not None else fallback
    container = AppContainer(event=event, state=state, ledger=stock)
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



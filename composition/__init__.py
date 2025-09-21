from typing import Optional, Any

from ..adapters.factory.registry import default as fallback
from ..application.log.emit import calibrate
from ..infrastructure.config import SETTINGS
from ..infrastructure.di.container import AppContainer
from ..infrastructure.locks import configure
from ..presentation.navigator import Navigator
from ..presentation.telegram.scope import make_scope as forge


async def assemble(event: Any, state: Any, registry: Optional[Any] = None) -> Navigator:
    calibrate(SETTINGS.log_redaction_mode)
    configure()
    reg = registry if registry is not None else fallback
    container = AppContainer(event=event, state=state, registry=reg)
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



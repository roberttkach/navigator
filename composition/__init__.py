from typing import Optional, Any

from ..adapters.factory.registry import default as reg_default
from ..application.log.emit import set_redaction_mode
from ..infrastructure.config import SETTINGS
from ..infrastructure.di.container import AppContainer
from ..infrastructure.locks import configure
from ..presentation.navigator import Navigator
from ..presentation.telegram.scope import make_scope


async def assemble(event: Any, state: Any, registry: Optional[Any] = None) -> Navigator:
    set_redaction_mode(SETTINGS.log_redaction_mode)
    configure()
    reg = registry if registry is not None else reg_default
    container = AppContainer(event=event, state=state, registry=reg)
    scope = make_scope(event)
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



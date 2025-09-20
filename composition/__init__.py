from typing import Optional, Any

from ..adapters.factory.registry import default as reg_default
from ..application.log.emit import set_redaction_mode
from ..composition import migrate
from ..infrastructure.config import SETTINGS
from ..infrastructure.di.container import AppContainer
from ..infrastructure.locks import configure_from_env
from ..presentation.navigator import Navigator
from ..presentation.telegram.scope import make_scope


async def create_navigator(event: Any, state: Any, registry: Optional[Any] = None) -> Navigator:
    set_redaction_mode(SETTINGS.log_redaction_mode)
    configure_from_env()
    reg = registry if registry is not None else reg_default
    await migrate.run(state, reg)
    container = AppContainer(event=event, state=state, registry=reg)
    scope = make_scope(event)
    return Navigator(
        add_uc=container.add_uc(),
        replace_uc=container.replace_uc(),
        back_uc=container.back_uc(),
        set_uc=container.set_uc(),
        pop_uc=container.pop_uc(),
        rebase_uc=container.rebase_uc(),
        last_uc=container.last_uc(),
        gateway=container.gateway(),
        scope=scope,
    )

"""Telegram presentation bindings."""

from .instrumentation import (
    build_retreat_instrument,
    instrument_for_configurator,
    instrument_for_router,
)
from .middleware import NavigatorMiddleware
from .router import (
    BACK_CALLBACK_DATA,
    NavigatorBack,
    RetreatCallback,
    RetreatDependencies,
    build_retreat_handler,
    configure_retreat,
    router,
)
from .scope import outline

instrument = instrument_for_router(router)

__all__ = [
    "router",
    "NavigatorBack",
    "BACK_CALLBACK_DATA",
    "RetreatCallback",
    "RetreatDependencies",
    "build_retreat_handler",
    "configure_retreat",
    "build_retreat_instrument",
    "instrument",
    "instrument_for_configurator",
    "instrument_for_router",
    "NavigatorMiddleware",
    "outline",
]

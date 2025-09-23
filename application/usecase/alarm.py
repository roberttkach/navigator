import logging
from typing import Callable

from ..log.emit import jlog
from ...domain.port.message import MessageGateway
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Alarm:
    def __init__(self, gateway: MessageGateway, alert: Callable[[Scope], str]) -> None:
        self._gateway = gateway
        self._alert = alert

    async def execute(self, scope: Scope, text: str | None = None) -> None:
        message = text if text is not None else self._alert(scope)
        if not message:
            return
        await self._gateway.alert(scope, message)
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_EMPTY,
            op="alarm",
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )

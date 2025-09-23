import logging
from typing import Callable

from ..log.emit import jlog
from ...domain.port.message import AlertPayload, MessageGateway
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Alarm:
    def __init__(self, gateway: MessageGateway, alert: Callable[[Scope], AlertPayload]) -> None:
        self._gateway = gateway
        self._alert = alert

    async def execute(self, scope: Scope) -> None:
        payload = self._alert(scope)
        await self._gateway.alert(scope, payload)
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_EMPTY,
            op="alarm",
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )

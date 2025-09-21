import logging

from ..log.emit import jlog
from ...domain.port.message import MessageGateway
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Alarm:
    def __init__(self, gateway: MessageGateway) -> None:
        self._gateway = gateway

    async def execute(self, scope: Scope) -> None:
        await self._gateway.alert(scope)
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_EMPTY,
            op="alarm",
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )

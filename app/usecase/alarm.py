import logging
from typing import Callable

from ...core.port.message import MessageGateway
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.message import Scope


class Alarm:
    def __init__(
        self,
        gateway: MessageGateway,
        alert: Callable[[Scope], str],
        telemetry: Telemetry,
    ) -> None:
        self._gateway = gateway
        self._alert = alert
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def execute(self, scope: Scope, text: str | None = None) -> None:
        message = text if text is not None else self._alert(scope)
        if not message:
            return
        await self._gateway.alert(scope, message)
        self._channel.emit(
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_OK,
            op="alarm",
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )

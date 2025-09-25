import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from navigator.app.usecase.set import Setter
from navigator.core.telemetry import Telemetry
from navigator.core.value.content import Payload


class StubTelemetryPort:
    def calibrate(self, mode: str) -> None:
        return None

    def emit(self, *args, **kwargs) -> None:
        return None


def make_setter(*, payload_return):
    ledger = SimpleNamespace(recall=AsyncMock(return_value=[SimpleNamespace(state="goal", messages=[])]), archive=AsyncMock())
    status = SimpleNamespace(assign=AsyncMock(), payload=AsyncMock(return_value=payload_return))
    gateway = SimpleNamespace()
    restorer = SimpleNamespace(revive=AsyncMock(return_value=[Payload(text="ok")]))
    planner = SimpleNamespace(render=AsyncMock(return_value=None))
    latest = SimpleNamespace(mark=AsyncMock())
    telemetry = Telemetry(StubTelemetryPort())
    return Setter(
        ledger=ledger,
        status=status,
        gateway=gateway,
        restorer=restorer,
        planner=planner,
        latest=latest,
        telemetry=telemetry,
    ), restorer


def test_revive_merges_none_payload_with_context():
    setter, restorer = make_setter(payload_return=None)

    asyncio.run(setter._revive(SimpleNamespace(state="goal"), {"foo": "bar"}, inline=False))

    assert restorer.revive.await_args.args[1] == {"foo": "bar"}

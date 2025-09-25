"""Bootstrap the Navigator runtime for telegram entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from navigator.adapters.telemetry.logger import PythonLoggingTelemetry
from navigator.api.contracts import ScopeDTO, ViewLedgerDTO
from navigator.core.port.factory import ViewForge, ViewLedger
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.infra.di.container import AppContainer
from navigator.presentation.alerts import missing
from navigator.presentation.bootstrap.navigator import compose
from navigator.presentation.navigator import Navigator
from typing import Any, cast


class _LedgerAdapter(ViewLedger):
    """Expose a DTO-backed ledger through the domain ``ViewLedger``."""

    def __init__(self, ledger: ViewLedgerDTO) -> None:
        self._ledger = ledger

    def get(self, key: str) -> ViewForge:
        """Return a forge callable for ``key`` ensuring callability."""

        forge = self._ledger.get(key)
        if not callable(forge):
            raise TypeError(f"Ledger forge for '{key}' is not callable")
        return cast(ViewForge, forge)

    def has(self, key: str) -> bool:
        """Return ``True`` when the underlying ledger exposes ``key``."""

        return bool(self._ledger.has(key))


def _scope(dto: ScopeDTO) -> Scope:
    """Translate external ``ScopeDTO`` structures into domain scopes."""

    return Scope(
        chat=getattr(dto, "chat", None),
        lang=getattr(dto, "lang", None),
        inline=getattr(dto, "inline", None),
        business=getattr(dto, "business", None),
        category=getattr(dto, "category", None),
        topic=getattr(dto, "topic", None),
        direct=bool(getattr(dto, "direct", False)),
    )


@dataclass(frozen=True)
class BootstrapContext:
    """Collect payloads required to assemble the navigator runtime."""

    event: Any
    state: Any
    ledger: ViewLedgerDTO
    scope: ScopeDTO


class TelemetryFactory:
    """Build calibrated telemetry instances for the runtime."""

    def create(self) -> Telemetry:
        port = PythonLoggingTelemetry()
        return Telemetry(port)


class ContainerFactory:
    """Construct application containers for the navigator runtime."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._telemetry = telemetry

    def create(self, context: BootstrapContext) -> AppContainer:
        return AppContainer(
            event=context.event,
            state=context.state,
            ledger=_LedgerAdapter(context.ledger),
            alert=missing,
            telemetry=self._telemetry,
        )


class NavigatorAssembler:
    """Compose navigator instances from bootstrap context."""

    def __init__(self, telemetry_factory: TelemetryFactory | None = None) -> None:
        self._telemetry_factory = telemetry_factory or TelemetryFactory()

    async def build(self, context: BootstrapContext) -> Navigator:
        telemetry = self._telemetry_factory.create()
        container = ContainerFactory(telemetry).create(context)
        settings = container.core().settings()
        mode = getattr(settings, "redaction", "")
        telemetry.calibrate(mode)
        from navigator.presentation.telegram import instrument

        instrument(telemetry)
        return compose(container, _scope(context.scope))


async def assemble(
        *,
        event: Any,
        state: Any,
        ledger: ViewLedgerDTO,
        scope: ScopeDTO,
) -> Navigator:
    """Construct a Navigator instance from entrypoint payloads."""

    context = BootstrapContext(event=event, state=state, ledger=ledger, scope=scope)
    assembler = NavigatorAssembler()
    return await assembler.build(context)


__all__ = [
    "BootstrapContext",
    "NavigatorAssembler",
    "TelemetryFactory",
    "assemble",
]

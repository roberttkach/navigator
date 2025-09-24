from __future__ import annotations

from dependency_injector import containers, providers

from navigator.adapters.storage.fsm import Chronicle, Latest, Status
from navigator.app.map.entry import EntryMapper
from navigator.core.telemetry import Telemetry


class StorageContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    chronicle = providers.Factory(Chronicle, state=core.state, telemetry=telemetry)
    status = providers.Factory(Status, state=core.state, telemetry=telemetry)
    latest = providers.Factory(Latest, state=core.state, telemetry=telemetry)
    mapper = providers.Factory(EntryMapper, ledger=core.ledger)


__all__ = ["StorageContainer"]

from __future__ import annotations

from dependency_injector import containers, providers

from ...adapters.storage.fsm import Chronicle, Latest, Status
from ...application.map.entry import EntryMapper


class StorageContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()

    chronicle = providers.Factory(Chronicle, state=core.state)
    status = providers.Factory(Status, state=core.state)
    latest = providers.Factory(Latest, state=core.state)
    mapper = providers.Factory(EntryMapper, ledger=core.ledger)


__all__ = ["StorageContainer"]

"""Facade around edit execution collaborators."""

from __future__ import annotations

from navigator.core.entity.history import Entry, Message
from navigator.core.service.rendering import decision
from navigator.core.typing.result import Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .execution import EditComponents, Execution, build_edit_components


class EditExecutor:
    """Dispatch reconciliation decisions to the Telegram gateway."""

    def __init__(self, components: EditComponents) -> None:
        self._components = components

    @classmethod
    def create(
        cls,
        gateway,
        telemetry,
        *,
        dispatcher=None,
        errors=None,
        refiner=None,
        cleanup=None,
    ) -> "EditExecutor":
        components = build_edit_components(
            gateway,
            telemetry,
            dispatcher=dispatcher,
            errors=errors,
            refiner=refiner,
            cleanup=cleanup,
        )
        return cls(components)

    async def execute(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        last: Entry | Message | None,
    ) -> Execution | None:
        """Apply ``verdict`` using the gateway and return execution metadata."""

        return await self._components.operation.apply(scope, verdict, payload, last)

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        await self._components.cleanup.delete(scope, identifiers)

    def refine(
        self,
        execution: Execution,
        verdict: decision.Decision,
        payload: Payload,
    ) -> Meta:
        """Reconcile execution metadata with persisted message state."""

        return self._components.refiner.refine(execution, verdict, payload)


__all__ = ["EditExecutor", "Execution", "EditComponents", "build_edit_components"]


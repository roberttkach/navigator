"""Facade aggregating container bindings for runtime access."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot

from .bindings import CoreBindings, IntegrationBindings, RuntimeBindings, UseCaseBindings
from .runtime import NavigatorRuntimeContainer


@dataclass(slots=True)
class AppContainer:
    """Aggregate binding containers without exposing infrastructure details."""

    core: CoreBindings
    integration: IntegrationBindings
    usecases: UseCaseBindings
    runtime_bindings: RuntimeBindings

    def runtime(self) -> NavigatorRuntimeContainer:
        """Expose runtime bindings produced by the application composition root."""

        return self.runtime_bindings.runtime()

    def snapshot(self) -> NavigatorRuntimeSnapshot:
        """Return the runtime snapshot without exposing container internals."""

        runtime = self.runtime()
        return runtime.snapshot()


__all__ = ["AppContainer"]

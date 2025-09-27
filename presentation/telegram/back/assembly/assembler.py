"""Assembler coordinating retreat handler collaborator resolution."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from ..handler import RetreatHandler
from ..protocols import Translator
from .overrides import RetreatHandlerOverrides
from .providers import RetreatHandlerProviders
from .resolution import RetreatHandlerResolution
from .workflow import RetreatWorkflowBundle


@dataclass(slots=True)
class RetreatHandlerAssembler:
    """Assemble retreat handlers while delegating collaborator resolution."""

    providers: RetreatHandlerProviders

    def assemble(
        self,
        *,
        telemetry: Telemetry,
        translator: Translator,
        overrides: RetreatHandlerOverrides | None = None,
    ) -> RetreatHandler:
        """Return a fully assembled retreat handler."""

        options = overrides or RetreatHandlerOverrides()
        bundle = RetreatWorkflowBundle.from_overrides(options, self.providers)
        resolution = RetreatHandlerResolution(
            telemetry=telemetry,
            translator=translator,
            providers=self.providers,
            overrides=options,
        )
        orchestrator = resolution.resolve_orchestrator(bundle)
        outcomes = resolution.resolve_outcomes()
        return RetreatHandler(orchestrator=orchestrator, outcomes=outcomes)


__all__ = ["RetreatHandlerAssembler"]

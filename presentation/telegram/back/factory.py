"""Factories assembling retreat handlers with dependency overrides."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from .assembly import (
    RetreatHandlerAssembler,
    RetreatHandlerOverrides,
    RetreatHandlerProviders,
)
from .handler import RetreatHandler
from .protocols import Translator


@dataclass(slots=True)
class RetreatHandlerFactory:
    """Create retreat handlers while isolating assembly responsibilities."""

    telemetry: Telemetry
    translator: Translator
    assembler: RetreatHandlerAssembler

    def create(
        self,
        *,
        overrides: RetreatHandlerOverrides | None = None,
    ) -> RetreatHandler:
        """Return a retreat handler assembled by the configured collaborators."""

        return self.assembler.assemble(
            telemetry=self.telemetry,
            translator=self.translator,
            overrides=overrides,
        )


def create_retreat_handler(
    telemetry: Telemetry,
    translator: Translator,
    *,
    providers: RetreatHandlerProviders,
    overrides: RetreatHandlerOverrides | None = None,
) -> RetreatHandler:
    """Convenience wrapper returning an assembled retreat handler."""

    assembler = RetreatHandlerAssembler(providers=providers)
    factory = RetreatHandlerFactory(
        telemetry=telemetry,
        translator=translator,
        assembler=assembler,
    )
    return factory.create(overrides=overrides)


__all__ = [
    "RetreatHandlerFactory",
    "RetreatHandlerOverrides",
    "RetreatHandlerProviders",
    "create_retreat_handler",
]

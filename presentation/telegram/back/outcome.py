"""Outcome utilities for telegram retreat handling."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import CallbackQuery

from .protocols import Translator
from .result import RetreatResult


@dataclass(frozen=True)
class RetreatOutcome:
    """Represents Telegram answer parameters for retreat operations."""

    text: str | None = None
    show_alert: bool = False


class RetreatOutcomeFactory:
    """Convert retreat results into Telegram-friendly outcomes."""

    def __init__(self, translator: Translator) -> None:
        self._translate = translator

    def success(self) -> RetreatOutcome:
        return RetreatOutcome()

    def failure(self, note: str, cb: CallbackQuery) -> RetreatOutcome:
        tongue = self._tongue(cb)
        key = "barred" if note == "barred" else "missing"
        return RetreatOutcome(text=self._translate(key, tongue), show_alert=True)

    def render(self, result: RetreatResult, cb: CallbackQuery) -> RetreatOutcome:
        if result.success:
            return self.success()
        return self.failure(result.note or "generic", cb)

    @staticmethod
    def _tongue(obj: CallbackQuery) -> str:
        user = getattr(obj, "from_user", None)
        code = getattr(user, "language_code", None)
        return (code or "en").split("-")[0].lower()


__all__ = ["RetreatOutcome", "RetreatOutcomeFactory"]

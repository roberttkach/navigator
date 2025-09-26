"""Policies describing how edit errors should be resolved."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from navigator.core.error import (
    CaptionOverflow,
    EditForbidden,
    EmptyPayload,
    ExtraForbidden,
    MessageUnchanged,
    TextOverflow,
)


class EditResolutionAction(Enum):
    """Actions available to resolve recoverable edit failures."""

    IGNORE = auto()
    RESEND = auto()


@dataclass(frozen=True, slots=True)
class EditResolution:
    """Describe telemetry side-effects and the desired recovery action."""

    action: EditResolutionAction
    skip_reason: str | None = None
    event: str | None = None
    inline_block_reason: str | None = None

    @classmethod
    def skip(cls, reason: str) -> "EditResolution":
        """Return a resolution that only reports a skip reason."""

        return cls(action=EditResolutionAction.IGNORE, skip_reason=reason)

    @classmethod
    def resend(
        cls, *, event: str | None = None, inline_block_reason: str | None = None
    ) -> "EditResolution":
        """Return a resolution that attempts a resend through fallback."""

        return cls(
            action=EditResolutionAction.RESEND,
            event=event,
            inline_block_reason=inline_block_reason,
        )

    @classmethod
    def ignore(
        cls, *, event: str | None = None, inline_block_reason: str | None = None
    ) -> "EditResolution":
        """Return a resolution that acknowledges the error without resending."""

        return cls(
            action=EditResolutionAction.IGNORE,
            event=event,
            inline_block_reason=inline_block_reason,
        )


class EditErrorPolicy:
    """Classify recoverable edit errors into actionable resolutions."""

    def resolve(self, error: Exception) -> EditResolution | None:
        """Return a resolution for ``error`` or ``None`` when it is unknown."""

        if isinstance(error, EmptyPayload):
            return EditResolution.skip("empty_payload")
        if isinstance(error, ExtraForbidden):
            return EditResolution.skip("extra_validation_failed")
        if isinstance(error, (TextOverflow, CaptionOverflow)):
            return EditResolution.skip("too_long")
        if isinstance(error, EditForbidden):
            return EditResolution.resend(
                event="edit_forbidden", inline_block_reason="inline_no_fallback"
            )
        if isinstance(error, MessageUnchanged):
            return EditResolution.ignore(
                event="not_modified", inline_block_reason="inline_no_fallback"
            )
        return None


__all__ = ["EditErrorPolicy", "EditResolution", "EditResolutionAction"]


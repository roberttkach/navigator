"""Decide how to reconcile stored history with incoming payloads."""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from .config import RenderingConfig
from .helpers import match
from ...value.content import Payload, caption
from .media_profile import identical_media, profile_media, requires_delete_send
from .normalization import (
    NormalizedView,
    preview_payload,
    text_content,
    textual_extras,
    view_of,
)


class Decision(Enum):
    """Possible reconciliation outcomes for an updated entry."""

    RESEND = auto()
    EDIT_TEXT = auto()
    EDIT_MEDIA_CAPTION = auto()
    EDIT_MEDIA = auto()
    EDIT_MARKUP = auto()
    DELETE_SEND = auto()
    NO_CHANGE = auto()


def _decide_textual(prior: NormalizedView, fresh: NormalizedView) -> Decision:
    """Resolve reconciliation for purely textual payloads."""

    if (text_content(prior) or "") == (text_content(fresh) or ""):
        if (
                (textual_extras(prior) != textual_extras(fresh))
                or (preview_payload(prior) != preview_payload(fresh))
        ):
            return Decision.EDIT_TEXT
        aligned = match(prior.reply, fresh.reply)
        return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP

    return Decision.EDIT_TEXT


def _decide_media(
        prior: NormalizedView,
        fresh: NormalizedView,
        config: RenderingConfig,
) -> Decision:
    """Resolve reconciliation for payloads carrying media objects."""

    if identical_media(prior, fresh, config.identity):
        before = profile_media(prior, config)
        after = profile_media(fresh, config)

        if before.edit != after.edit:
            return Decision.EDIT_MEDIA

        if (
                (caption(prior) or "") == (caption(fresh) or "")
                and textual_extras(prior) == textual_extras(fresh)
                and before.caption == after.caption
        ):
            aligned = match(prior.reply, fresh.reply)
            return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP
        return Decision.EDIT_MEDIA_CAPTION

    return Decision.EDIT_MEDIA


def decide(old: Optional[object], new: Payload, config: RenderingConfig) -> Decision:
    """Select an edit strategy that reconciles history with new content."""

    if not old:
        return Decision.RESEND

    prior = view_of(old)
    fresh = view_of(new)

    if requires_delete_send(prior, fresh):
        return Decision.DELETE_SEND

    if not prior.is_media_payload and not fresh.is_media_payload:
        return _decide_textual(prior, fresh)

    if prior.is_media_payload and fresh.is_media_payload:
        return _decide_media(prior, fresh, config)

    return Decision.NO_CHANGE

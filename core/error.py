from __future__ import annotations


class NavigatorError(Exception):
    """Represent navigator domain errors."""


class HistoryEmpty(NavigatorError):
    """Signal that history is too short for the requested operation."""


class StateNotFound(NavigatorError):
    """Report that a requested state could not be located."""

    def __init__(self, state: str | None = None):
        message = "state_not_found" if state is None else f"state_not_found:{state}"
        super().__init__(message)
        self.state = state


class EditForbidden(NavigatorError):
    def __init__(self, code: str | None = None):
        super().__init__(code or "edit_forbidden")
        self.code = code or "edit_forbidden"


class MessageUnchanged(NavigatorError):
    """Report an edit that produced no changes."""


class InlineUnsupported(NavigatorError):
    """Reject operations that are not supported inline."""


class EmptyPayload(NavigatorError):
    """Reject attempts to send or edit with empty payload."""


class TextOverflow(NavigatorError):
    """Signal that text payload exceeds gateway limits."""


class CaptionOverflow(NavigatorError):
    """Signal that caption payload exceeds gateway limits."""


class ExtraForbidden(NavigatorError):
    """Reject extra payload that the codec disallows."""


class MetadataError(NavigatorError):
    """Represent errors encountered while mapping metadata."""


class MetadataKindMissing(MetadataError):
    def __init__(self) -> None:
        super().__init__("metadata_kind_missing")


class MetadataKindUnsupported(MetadataError):
    def __init__(self, kind: str | None = None) -> None:
        tag = kind or "unknown"
        super().__init__(f"metadata_kind_unsupported:{tag}")
        self.kind = kind


class MetadataMediumMissing(MetadataError):
    def __init__(self) -> None:
        super().__init__("metadata_medium_missing")


class MetadataGroupMediumMissing(MetadataError):
    def __init__(self) -> None:
        super().__init__("metadata_group_medium_missing")


__all__ = [
    "NavigatorError",
    "HistoryEmpty",
    "EditForbidden",
    "MessageUnchanged",
    "InlineUnsupported",
    "EmptyPayload",
    "TextOverflow",
    "CaptionOverflow",
    "ExtraForbidden",
    "StateNotFound",
    "MetadataError",
    "MetadataKindMissing",
    "MetadataKindUnsupported",
    "MetadataMediumMissing",
    "MetadataGroupMediumMissing",
]

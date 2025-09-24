from __future__ import annotations


class NavigatorError(Exception):
    """Base error for navigator domain."""


class HistoryEmpty(NavigatorError):
    """History is too short to perform the operation."""


class StateNotFound(NavigatorError):
    """Requested state is missing from history."""

    def __init__(self, state: str | None = None):
        message = "state_not_found" if state is None else f"state_not_found:{state}"
        super().__init__(message)
        self.state = state


class EditForbidden(NavigatorError):
    def __init__(self, code: str | None = None):
        super().__init__(code or "edit_forbidden")
        self.code = code or "edit_forbidden"


class MessageUnchanged(NavigatorError):
    """Edit operation produced no changes."""


class InlineUnsupported(NavigatorError):
    """Operation is not supported in inline context."""


class EmptyPayload(NavigatorError):
    """Attempt to send or edit with empty payload."""


class TextOverflow(NavigatorError):
    """Text payload exceeds gateway limits."""


class CaptionOverflow(NavigatorError):
    """Caption payload exceeds gateway limits."""


class ExtraForbidden(NavigatorError):
    """Extra payload rejected by codec."""


class MetadataError(NavigatorError):
    """Base class for metadata mapping errors."""


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

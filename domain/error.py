class NavigatorError(Exception):
    """Base error for navigator domain."""
    pass


class HistoryEmpty(NavigatorError):
    """History is too short to perform the operation."""
    pass


class MessageEditForbidden(NavigatorError):
    def __init__(self, code: str | None = None):
        super().__init__(code or "edit_forbidden")
        self.code = code or "edit_forbidden"


class MessageNotChanged(NavigatorError):
    """Edit operation produced no changes."""
    pass


class InlineUnsupported(NavigatorError):
    """Operation is not supported in inline context."""
    pass


class EmptyPayload(NavigatorError):
    """Attempt to send or edit with empty payload."""
    pass


class TextTooLong(NavigatorError):
    pass


class CaptionTooLong(NavigatorError):
    pass


class ExtraKeyForbidden(NavigatorError):
    pass


__all__ = [
    "NavigatorError",
    "HistoryEmpty",
    "MessageEditForbidden",
    "MessageNotChanged",
    "InlineUnsupported",
    "EmptyPayload",
    "TextTooLong",
    "CaptionTooLong",
    "ExtraKeyForbidden",
]

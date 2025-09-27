"""Common exceptions for container bootstrap helpers."""
from __future__ import annotations


class ContainerResolutionError(LookupError):
    """Raised when default container collaborators cannot be resolved."""


__all__ = ["ContainerResolutionError"]

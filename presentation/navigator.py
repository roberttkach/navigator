"""Presentation level navigator facade."""
from __future__ import annotations

from navigator.app.service.navigator_runtime.facade import NavigatorFacade


class Navigator(NavigatorFacade):
    """Presentation-specific navigator facade."""

    pass


__all__ = ["Navigator"]

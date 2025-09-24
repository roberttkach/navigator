"""Navigator public API (framework-agnostic)."""

from .presentation.bootstrap.navigator import build_navigator
from .presentation.navigator import Navigator

__all__ = ["Navigator", "build_navigator"]

"""Navigator public API."""

from .infrastructure.bootstrap.assemble import assemble
from .presentation.navigator import Navigator

__all__ = ["Navigator", "assemble"]

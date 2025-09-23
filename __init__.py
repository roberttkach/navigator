"""Navigator public API.

Example:
    from navigator import assemble, registry

    navigator = await assemble(event, state, ledger=registry.default)
"""

from .adapters.factory import registry
from .composition import assemble
from .presentation.navigator import Navigator

__all__ = ["Navigator", "assemble", "registry"]

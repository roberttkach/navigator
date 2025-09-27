"""Define rendering options used during history reconciliation."""

from dataclasses import dataclass, field

from ...port.mediaid import MediaIdentityPolicy


class StringIdentityPolicy(MediaIdentityPolicy):
    """Match media payloads by a shared string identity."""

    def same(self, former: object, latter: object, *, type: str) -> bool:
        """Return ``True`` when both identifiers reference the same value."""

        del type
        return isinstance(former, str) and isinstance(latter, str) and former == latter


@dataclass(frozen=True, slots=True)
class RenderingConfig:
    """Capture knobs affecting render decisions and reconciliation."""

    thumbguard: bool = False
    identity: MediaIdentityPolicy = field(default_factory=StringIdentityPolicy)


__all__ = ["RenderingConfig", "StringIdentityPolicy"]

from dataclasses import dataclass, field

from ...port.mediaid import MediaIdentityPolicy


class _FileIdIdentity(MediaIdentityPolicy):
    def same(self, former: object, latter: object, *, type: str) -> bool:
        return isinstance(former, str) and isinstance(latter, str) and former == latter


@dataclass(frozen=True, slots=True)
class RenderingConfig:
    thumbguard: bool = False
    identity: MediaIdentityPolicy = field(default_factory=_FileIdIdentity)

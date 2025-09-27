"""Payload normalization helpers for add operations."""

from __future__ import annotations

from typing import List

from navigator.core.value.content import Payload, normalize
from navigator.core.value.message import Scope

from ...service.view.policy import adapt


class AppendPayloadAdapter:
    """Apply normalisation and scope-specific adjustments to payload bundles."""

    def normalize(self, scope: Scope, bundle: List[Payload]) -> List[Payload]:
        return [adapt(scope, normalize(payload)) for payload in bundle]


__all__ = ["AppendPayloadAdapter"]


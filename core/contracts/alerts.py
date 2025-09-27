"""Contracts describing alert callbacks shared across layers."""
from __future__ import annotations

from typing import Callable

from navigator.core.value.message import Scope

MissingAlert = Callable[[Scope], str]

__all__ = ["MissingAlert"]

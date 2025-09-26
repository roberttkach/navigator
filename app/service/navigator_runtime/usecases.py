"""Definitions for navigator use case bundles."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter


@dataclass(frozen=True)
class NavigatorUseCases:
    """Bundle of use cases required to assemble the navigator runtime."""

    appender: Appender
    swapper: Swapper
    rewinder: Rewinder
    setter: Setter
    trimmer: Trimmer
    shifter: Shifter
    tailer: Tailer
    alarm: Alarm


__all__ = ["NavigatorUseCases"]

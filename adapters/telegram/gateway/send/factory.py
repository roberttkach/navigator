"""Factory helpers assembling send dispatchers."""
from __future__ import annotations

from aiogram import Bot

from .dependencies import SendDependencies
from .dispatcher import SendDispatcher
from .guardian import LimitsGuardian
from .strategies import AlbumSender, SingleMediaSender, TextSender


class SendDispatcherFactory:
    """Build ``SendDispatcher`` instances from send dependencies."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._dependencies = dependencies

    def create(self, bot: Bot) -> SendDispatcher:
        guard = LimitsGuardian(self._dependencies.limits)
        album = AlbumSender(self._dependencies)
        media = SingleMediaSender(self._dependencies, guard)
        text = TextSender(self._dependencies, guard)
        return SendDispatcher(bot, album=album, media=media, text=text)


__all__ = ["SendDispatcherFactory"]

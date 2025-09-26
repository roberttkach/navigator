"""Dispatch helpers coordinating Telegram send strategies."""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from navigator.core.typing.result import Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .context import SendContext
from .strategies import AlbumSender, SingleMediaSender, TextSender


class SendDispatcher:
    """Execute Telegram send operations using prepared context."""

    def __init__(
        self,
        bot: Bot,
        *,
        album: AlbumSender,
        media: SingleMediaSender,
        text: TextSender,
    ) -> None:
        self._bot = bot
        self._albums = album
        self._media = media
        self._text = text

    async def dispatch(
        self,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        if payload.group:
            return await self._albums.send(
                self._bot,
                payload,
                scope=scope,
                context=context,
            )
        if payload.media:
            return await self._media.send(
                self._bot,
                payload,
                scope=scope,
                context=context,
                truncate=truncate,
            )
        return await self._text.send(
            self._bot,
            payload,
            scope=scope,
            context=context,
            truncate=truncate,
        )


__all__ = ["SendDispatcher"]

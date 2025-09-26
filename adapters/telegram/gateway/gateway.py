"""Telegram gateway facade aggregating dedicated collaborators."""
from __future__ import annotations

from navigator.core.port.message import MessageGateway, Result
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .deletion import TelegramDeletionManager
from .editor import TelegramMessageEditor
from .markup import TelegramMarkupRefiner
from .notifier import TelegramNotifier
from .sender import TelegramMessageSender


class TelegramGateway(MessageGateway):
    """Facade delegating Telegram operations to dedicated collaborators."""

    def __init__(
        self,
        *,
        sender: TelegramMessageSender,
        editor: TelegramMessageEditor,
        markup: TelegramMarkupRefiner,
        deletion: TelegramDeletionManager,
        notifier: TelegramNotifier,
    ) -> None:
        self._sender = sender
        self._editor = editor
        self._markup = markup
        self._deletion = deletion
        self._notifier = notifier

    async def send(self, scope: Scope, payload: Payload) -> Result:
        return await self._sender.send(scope, payload)

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.rewrite(scope, identifier, payload)

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.recast(scope, identifier, payload)

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.retitle(scope, identifier, payload)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._markup.remap(scope, identifier, payload)

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        await self._deletion.delete(scope, identifiers)

    async def alert(self, scope: Scope, text: str) -> None:
        await self._notifier.alert(scope, text)


__all__ = ["TelegramGateway"]

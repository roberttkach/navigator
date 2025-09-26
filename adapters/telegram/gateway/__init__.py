"""Telegram gateway package exposing facade and supporting builders."""
from __future__ import annotations

from .factory import create_gateway
from .gateway import TelegramGateway
from .sender import TelegramMessageSender
from .editor import TelegramMessageEditor
from .markup import TelegramMarkupRefiner
from .deletion import TelegramDeletionManager
from .notifier import TelegramNotifier

__all__ = [
    "TelegramGateway",
    "TelegramMessageEditor",
    "TelegramMessageSender",
    "TelegramMarkupRefiner",
    "TelegramDeletionManager",
    "TelegramNotifier",
    "create_gateway",
]

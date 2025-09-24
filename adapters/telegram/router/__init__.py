"""Telegram router utilities."""
from .aiogram import router, retreat, BACK_CALLBACK_DATA, NavigatorLike
from .lexicon import lexeme

__all__ = [
    "router",
    "retreat",
    "BACK_CALLBACK_DATA",
    "NavigatorLike",
    "lexeme",
]

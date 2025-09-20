from __future__ import annotations

import warnings
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scope:
    chat: int | None
    lang: str | None = None
    user: int | None = None
    id: int | None = None
    inline: str | None = None
    business: str | None = None
    category: str | None = None

    @property
    def user_id(self) -> int | None:
        warnings.warn("Scope.user_id is deprecated; use Scope.user", DeprecationWarning, stacklevel=2)
        return self.user

    @user_id.setter
    def user_id(self, value: int | None) -> None:
        warnings.warn("Scope.user_id is deprecated; use Scope.user", DeprecationWarning, stacklevel=2)
        self.user = value

    @property
    def inline_id(self) -> str | None:
        warnings.warn("Scope.inline_id is deprecated; use Scope.inline", DeprecationWarning, stacklevel=2)
        return self.inline

    @inline_id.setter
    def inline_id(self, value: str | None) -> None:
        warnings.warn("Scope.inline_id is deprecated; use Scope.inline", DeprecationWarning, stacklevel=2)
        self.inline = value

    @property
    def biz_id(self) -> str | None:
        warnings.warn("Scope.biz_id is deprecated; use Scope.business", DeprecationWarning, stacklevel=2)
        return self.business

    @biz_id.setter
    def biz_id(self, value: str | None) -> None:
        warnings.warn("Scope.biz_id is deprecated; use Scope.business", DeprecationWarning, stacklevel=2)
        self.business = value

    @property
    def chat_kind(self) -> str | None:
        warnings.warn("Scope.chat_kind is deprecated; use Scope.category", DeprecationWarning, stacklevel=2)
        return self.category

    @chat_kind.setter
    def chat_kind(self, value: str | None) -> None:
        warnings.warn("Scope.chat_kind is deprecated; use Scope.category", DeprecationWarning, stacklevel=2)
        self.category = value

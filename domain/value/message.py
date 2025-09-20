from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Scope:
    chat: Optional[int]
    lang: Optional[str] = None
    user_id: Optional[int] = None
    id: Optional[int] = None
    inline_id: Optional[str] = None
    biz_id: Optional[str] = None
    chat_kind: Optional[str] = None

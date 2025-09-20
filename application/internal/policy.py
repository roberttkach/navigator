from datetime import datetime, timezone
from typing import Literal
import warnings

from ...domain.entity.history import Entry, Msg
from ...domain.entity.media import MediaItem
from ...domain.service.history.extra import sanitize_extra
from ...domain.value.content import Payload, caption

SHIELD_MESSAGE = "Inline message does not support media groups"


def prime(id: int, payload: Payload) -> Entry:
    media = None
    if payload.media:
        media = MediaItem(type=payload.media.type, path=payload.media.path, caption=caption(payload))

    if payload.group:
        first = payload.group[0] if payload.group else None
        text_len = len((getattr(first, "caption", None) or ""))
    elif payload.media:
        text_len = len((caption(payload) or ""))
    elif isinstance(payload.text, str):
        text_len = len(payload.text)
    else:
        text_len = 0

    extra = sanitize_extra(payload.extra, text_len=text_len)
    msg = Msg(
        id=id,
        text=None if (payload.media or payload.group) else payload.text,
        media=media,
        group=payload.group,
        markup=None,
        preview=payload.preview,
        extra=extra,
        automated=True,
        ts=datetime.now(timezone.utc),
    )
    return Entry(
        state=None,
        view=None,
        messages=[msg],
    )


def shield(scope, payload):
    if getattr(scope, "inline", None) and getattr(payload, "group", None):
        from ...domain.error import InlineUnsupported
        raise InlineUnsupported(SHIELD_MESSAGE)


# Если True: при inline last.delete без удаления в Telegram
# выполняется срез последнего Entry из истории и сброс last_id.
TailPrune: bool = True

# Политика «хвоста» при inline back/set:
# keep   — оставлять как есть;
# delete — пытаться удалить «хвост» (только при наличии business);
# collapse — синоним delete (удаление при business; иначе поведение как keep).
TailMode: Literal["keep", "delete", "collapse"] = "keep"

# --- Флаги resend-фоллбека при неуспешном edit (не для inline) ---

# При MessageEditForbidden в non-inline выполняется send(new) + delete(old_id + extras)
ResendOnBan: bool = True

# При MessageNotChanged фоллбек по умолчанию выключен, чтобы не плодить дубликаты
ResendOnIdle: bool = False

# Разрешать имплицитный EDIT_MEDIA_CAPTION вместо DELETE_SEND при last.edit (non-inline)?
ImplicitCaption: bool = True  # для сохранения текущего поведения

# Поднимать исключения в swap() вместо тихого skip?
StrictAbort: bool = False  # для сохранения текущей семантики


def make_dummy_entry_for_last(id: int, payload: Payload) -> Entry:
    warnings.warn("make_dummy_entry_for_last is deprecated; use prime", DeprecationWarning, stacklevel=2)
    return prime(id, payload)


def inline_guard(scope, payload):
    warnings.warn("inline_guard is deprecated; use shield", DeprecationWarning, stacklevel=2)
    return shield(scope, payload)


INLINE_DELETE_TRIMS_HISTORY = TailPrune
INLINE_TAIL_MODE = TailMode
RESEND_FALLBACK_ON_FORBIDDEN = ResendOnBan
RESEND_FALLBACK_ON_NOT_MODIFIED = ResendOnIdle
IMPLICIT_MEDIA_TO_CAPTION = ImplicitCaption
STRICT_VALIDATION_FAIL = StrictAbort

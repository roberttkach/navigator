from datetime import datetime, timezone
from typing import Literal

from ...domain.entity.history import Entry, Msg
from ...domain.entity.media import MediaItem
from ...domain.value.content import Payload, caption_of

INLINE_GUARD_MESSAGE = "Inline message does not support media groups"


def make_dummy_entry_for_last(id: int, payload: Payload) -> Entry:
    media = None
    if payload.media:
        media = MediaItem(type=payload.media.type, path=payload.media.path, caption=caption_of(payload))
    msg = Msg(
        id=id,
        text=None if (payload.media or payload.group) else payload.text,
        media=media,
        group=payload.group,
        markup=None,
        preview=payload.preview,
        extra=payload.extra,
        by_bot=True,
        ts=datetime.now(timezone.utc),
    )
    return Entry(
        state=None,
        view=None,
        messages=[msg],
    )


def inline_guard(scope, payload):
    if getattr(scope, "inline_id", None) and getattr(payload, "group", None):
        from ...domain.error import InlineUnsupported
        raise InlineUnsupported(INLINE_GUARD_MESSAGE)


# Если True: при inline last.delete без удаления в Telegram
# выполняется срез последнего Entry из истории и сброс last_id.
INLINE_DELETE_TRIMS_HISTORY: bool = True

# Политика «хвоста» при inline back/set:
# keep   — оставлять как есть;
# delete — пытаться удалить «хвост» (только при наличии biz_id);
# collapse — синоним delete (удаление при biz_id; иначе поведение как keep).
INLINE_TAIL_MODE: Literal["keep", "delete", "collapse"] = "keep"

# --- Флаги resend-фоллбека при неуспешном edit (не для inline) ---

# При MessageEditForbidden в non-inline выполняется send(new) + delete(old_id + aux_ids)
RESEND_FALLBACK_ON_FORBIDDEN: bool = True

# При MessageNotChanged фоллбек по умолчанию выключен, чтобы не плодить дубликаты
RESEND_FALLBACK_ON_NOT_MODIFIED: bool = False

# Разрешать имплицитный EDIT_MEDIA_CAPTION вместо DELETE_SEND при last.edit (non-inline)?
IMPLICIT_MEDIA_TO_CAPTION: bool = True  # для сохранения текущего поведения

# Поднимать исключения в swap() вместо тихого skip?
STRICT_VALIDATION_FAIL: bool = False  # для сохранения текущей семантики

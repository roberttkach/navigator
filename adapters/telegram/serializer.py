from __future__ import annotations

import logging
from dataclasses import is_dataclass
from typing import Dict, Any, Optional

from aiogram.types import LinkPreviewOptions

from .extra import validate_extra, ALLOWED_TEXT, ALLOWED_CAPTION_TEXT
from .keyfilter import accept_for
from ...domain.entity.markup import Markup
from ...domain.log.emit import jlog
from ...domain.util.entities import validate_entities
from ...domain.value.content import Payload, caption_of
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def decode_reply(codec, reply):
    if isinstance(reply, Markup):
        return codec.decode(reply)
    return None


def map_preview(preview):
    if not preview:
        return None
    if is_dataclass(preview):
        return LinkPreviewOptions(
            url=preview.url,
            prefer_small_media=preview.small,
            prefer_large_media=preview.large,
            show_above_text=preview.above,
            is_disabled=preview.disabled,
        )
    return None


def caption_for(payload: Payload):
    return caption_of(payload)


def caption_for_edit(payload: Payload) -> Optional[str]:
    """
    Правило для edit_caption:
    - вернуть текст подписи, если он вычисляется (caption_of(payload));
    - если payload.clear_caption установлен — вернуть "" для очистки подписи;
    - иначе вернуть None (не менять подпись).
    Пустая строка → явная очистка подписи на стороне Telegram.
    Примечание: пустая строка из payload.text без маркера clear_caption игнорируется и приводит к no-op.
    """
    cap = caption_of(payload)
    if cap is not None:
        return cap
    if payload.clear_caption:
        return ""
    return None


def split_extra(extra: dict | None) -> tuple[dict, dict]:
    extra = extra or {}
    cap = {k: extra[k] for k in ("mode", "entities", "message_effect_id") if k in extra}
    med = {k: extra[k] for k in (
        "spoiler", "show_caption_above_media", "start", "thumb",
        "title", "performer", "duration", "width", "height"
    ) if k in extra}
    return cap, med


def sanitize_text_kwargs(
        extra: Dict[str, Any] | None,
        is_caption: bool,
        target=None,
        *,
        text_len: int | None = None,
) -> Dict[str, Any]:
    # При пустом тексте/подписи не отправлять parse_mode/entities
    if (text_len or 0) <= 0:
        return {}
    allowed = ALLOWED_CAPTION_TEXT if is_caption else ALLOWED_TEXT
    validate_extra(extra, allowed)
    kv = dict(extra or {})
    if "entities" in kv:
        cleaned = validate_entities(kv.get("entities"), text_len or 0)
        if cleaned:
            kv["entities"] = cleaned
        else:
            kv.pop("entities", None)
    if "mode" in kv and "entities" not in kv:
        kv["parse_mode"] = kv.pop("mode")
    if is_caption and "entities" in kv:
        kv["caption_entities"] = kv.pop("entities")
    if target is not None:
        filtered = accept_for(target, kv)
        if set(kv.keys()) != set(filtered.keys()):
            tgt = getattr(target, "__name__", str(target))
            jlog(
                logger,
                logging.DEBUG,
                LogCode.EXTRA_FILTERED_OUT,
                stage=f"{'edit' if 'edit' in tgt.lower() else 'send'}.{'caption' if is_caption else 'text'}",
                target=tgt,
                before=sorted(kv.keys()),
                after=sorted(filtered.keys()),
                filtered_keys=sorted(set(kv) - set(filtered)),
            )
        return filtered
    return kv


def normalize_extra_for(scope, extra: Dict[str, Any] | None, *, is_edit: bool) -> Optional[Dict[str, Any]]:
    """
    Нормализация extra:
    - message_effect_id удаляется при edit и во всех чатах, кроме private.
    - Следствие: попытка «поменять только эффект» (без изменения текста/медиа/markup) приводит к NO_CHANGE.
    - Прочие ключи передаются без изменений.
    """
    if not extra:
        return None
    d = dict(extra)
    ct = getattr(scope, "chat_kind", None)
    if "message_effect_id" in d and (is_edit or ct != "private"):
        d.pop("message_effect_id", None)
        # Лог-маркер: эффект удалён нормализацией
        jlog(logger, logging.DEBUG, LogCode.EXTRA_EFFECT_STRIPPED, note="effect_stripped")
    return d

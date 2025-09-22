from __future__ import annotations

import logging
from dataclasses import is_dataclass
from typing import Dict, Any, Optional

from aiogram.types import LinkPreviewOptions

from .extra import audit, ALLOWED_TEXT, ALLOWED_CAPTION_TEXT
from .screen import screen
from ...domain.entity.markup import Markup
from ...domain.log.emit import jlog
from ...domain.util.entities import sanitize
from ...domain.value import content
from ...domain.value.content import Payload
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def decode(codec, reply):
    if isinstance(reply, Markup):
        return codec.decode(reply)
    return None


def preview(preview):
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


def caption(payload: Payload):
    return content.caption(payload)


def restate(payload: Payload) -> Optional[str]:
    """
    Правило для retitle:
    - вернуть текст подписи, если он вычисляется (caption(payload));
    - если payload.erase установлен — вернуть "" для очистки подписи;
    - иначе вернуть None (не менять подпись).
    Пустая строка → явная очистка подписи на стороне Telegram.
    Примечание: пустая строка из payload.text без маркера erase игнорируется и приводит к no-op.
    """
    cap = content.caption(payload)
    if cap is not None:
        return cap
    if payload.erase:
        return ""
    return None


def divide(extra: dict | None) -> dict[str, dict]:
    extra = extra or {}
    caption = {k: extra[k] for k in ("mode", "entities", "message_effect_id") if k in extra}
    media = {
        k: extra[k]
        for k in (
            "spoiler",
            "show_caption_above_media",
            "start",
            "thumb",
            "title",
            "performer",
            "duration",
            "width",
            "height",
        )
        if k in extra
    }
    return {"caption": caption, "media": media}


def cleanse(
    extra: Dict[str, Any] | None,
    captioning: bool,
    target=None,
    *,
    length: int | None = None,
) -> Dict[str, Any]:
    if (length or 0) <= 0:
        return {}
    allowed = ALLOWED_CAPTION_TEXT if captioning else ALLOWED_TEXT
    audit(extra, allowed)
    mapping = dict(extra or {})
    if "entities" in mapping:
        sanitized = sanitize(mapping.get("entities"), length or 0)
        if sanitized:
            mapping["entities"] = sanitized
        else:
            mapping.pop("entities", None)
    if "mode" in mapping and "entities" not in mapping:
        mapping["parse_mode"] = mapping.pop("mode")
    if captioning and "entities" in mapping:
        mapping["caption_entities"] = mapping.pop("entities")
    if target is not None:
        screened = screen(target, mapping)
        if set(mapping.keys()) != set(screened.keys()):
            name = getattr(target, "__name__", str(target))
            jlog(
                logger,
                logging.DEBUG,
                LogCode.EXTRA_FILTERED_OUT,
                stage=f"{'edit' if 'edit' in name.lower() else 'send'}.{'caption' if captioning else 'text'}",
                target=name,
                before=sorted(mapping.keys()),
                after=sorted(screened.keys()),
                filtered_keys=sorted(set(mapping) - set(screened)),
            )
        return screened
    return mapping


def scrub(scope, extra: Dict[str, Any] | None, *, editing: bool) -> Optional[Dict[str, Any]]:
    """
    Нормализация extra:
    - message_effect_id удаляется при edit и во всех чатах, кроме private.
    - Следствие: попытка «поменять только эффект» (без изменения текста/медиа/markup) приводит к NO_CHANGE.
    - Прочие ключи передаются без изменений.
    """
    if not extra:
        return None
    mapping = dict(extra)
    category = getattr(scope, "category", None)
    if "message_effect_id" in mapping and (editing or category != "private"):
        mapping.pop("message_effect_id", None)
        jlog(logger, logging.DEBUG, LogCode.EXTRA_EFFECT_STRIPPED, note="effect_stripped")
    return mapping

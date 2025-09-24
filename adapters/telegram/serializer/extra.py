from __future__ import annotations

from typing import Any, Dict

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.service.history.extra import cleanse as history_cleanse
from navigator.core.util.entities import sanitize
from navigator.core.value.message import Scope


class TelegramExtraSchema(ExtraSchema):
    def send(
        self,
        scope: Scope,
        extra: dict | None,
        *,
        caption_len: int,
        media: bool,
    ) -> dict:
        return self._compose(scope, extra, caption_len, media, editing=False)

    def edit(
        self,
        scope: Scope,
        extra: dict | None,
        *,
        caption_len: int,
        media: bool,
    ) -> dict:
        return self._compose(scope, extra, caption_len, media, editing=True)

    def history(self, extra: dict | None, *, length: int) -> dict | None:
        return history_cleanse(extra, length=length)

    def _compose(
        self,
        scope: Scope,
        extra: dict | None,
        length: int,
        media: bool,
        *,
        editing: bool,
    ) -> dict:
        mapping = dict(extra or {})
        effect = self._effect(scope, mapping, editing=editing)
        text_block: Dict[str, Any] = {}
        caption_block: Dict[str, Any] = {}
        media_block: Dict[str, Any] = {}

        if media:
            caption_block = self._caption(mapping, length)
            media_block = self._media(mapping)
        else:
            text_block = self._text(mapping, length)

        if effect and media:
            caption_block["message_effect_id"] = effect
        elif effect:
            text_block["message_effect_id"] = effect

        return {
            "text": text_block,
            "caption": caption_block,
            "media": media_block,
            "effect": effect,
        }

    @staticmethod
    def _effect(scope: Scope, extra: Dict[str, Any], *, editing: bool) -> str | None:
        effect = extra.pop("message_effect_id", None)
        if effect is None:
            return None
        category = getattr(scope, "category", None)
        if editing or category != "private":
            return None
        return str(effect)

    @staticmethod
    def _mode(block: Dict[str, Any]) -> str | None:
        mode = block.get("mode")
        if mode in {"HTML", "MarkdownV2"}:
            return mode
        return None

    def _text(self, extra: Dict[str, Any], length: int) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        mode = self._mode(extra)
        if mode:
            fields["parse_mode"] = mode
        entities = self._entities(extra, length)
        if entities:
            fields["entities"] = entities
        return fields

    def _caption(self, extra: Dict[str, Any], length: int) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        mode = self._mode(extra)
        if mode:
            fields["parse_mode"] = mode
        entities = self._entities(extra, length)
        if entities:
            fields["caption_entities"] = entities
        return fields

    @staticmethod
    def _media(extra: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "spoiler",
            "show_caption_above_media",
            "start",
            "thumb",
            "title",
            "performer",
            "duration",
            "width",
            "height",
            "cover",
            "supports_streaming",
        }
        return {key: extra[key] for key in allowed if key in extra}

    @staticmethod
    def _entities(extra: Dict[str, Any], length: int):
        entities = extra.get("entities")
        if not entities:
            return None
        return sanitize(entities, length or 0) or None


__all__ = ["TelegramExtraSchema"]

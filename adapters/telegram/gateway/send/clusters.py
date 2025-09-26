"""Helpers building payload clusters from Telegram responses."""
from __future__ import annotations

from aiogram.types import Message

from navigator.core.typing.result import Cluster
from navigator.core.value.content import Payload


class GroupClusterBuilder:
    """Construct media group clusters from Telegram messages."""

    def build(self, messages: list[Message], payload: Payload) -> list[Cluster]:
        clusters: list[Cluster] = []
        for index, message in enumerate(messages):
            member = payload.group[index] if payload.group and index < len(payload.group) else None
            medium, filetoken = self._member_tokens(message, member)
            clusters.append(
                Cluster(
                    medium=medium,
                    file=filetoken,
                    caption=message.caption if index == 0 else "",
                )
            )
        return clusters

    def _member_tokens(self, message: Message, member) -> tuple[str | None, str | None]:
        medium = None
        filetoken = None
        if message.photo:
            medium = "photo"
            filetoken = message.photo[-1].file_id
        elif message.video:
            medium = "video"
            filetoken = message.video.file_id
        elif message.animation:
            medium = "animation"
            filetoken = message.animation.file_id
        elif message.document:
            medium = "document"
            filetoken = message.document.file_id
        elif message.audio:
            medium = "audio"
            filetoken = message.audio.file_id
        elif message.voice:
            medium = "voice"
            filetoken = message.voice.file_id
        elif message.video_note:
            medium = "video_note"
            filetoken = message.video_note.file_id

        if medium is None and member is not None:
            medium = getattr(getattr(member, "type", None), "value", None)
        if filetoken is None and member is not None:
            path = getattr(member, "path", None)
            if isinstance(path, str):
                filetoken = path
        return medium, filetoken


__all__ = ["GroupClusterBuilder"]

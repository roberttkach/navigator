"""Composition of Telegram media objects."""

from __future__ import annotations

from navigator.core.entity.media import MediaItem
from navigator.core.error import CaptionOverflow
from navigator.core.port.limits import Limits
from navigator.core.port.pathpolicy import MediaPathPolicy

from .policy import convert
from ..serializer.screen import SignatureScreen
from .settings import MediaSettingsNormalizer
from .types import InputMedia, select_handler


class MediaComposer:
    """Compose media payloads with caption and metadata constraints."""

    def __init__(
        self,
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        limits: Limits,
    ) -> None:
        self._policy = policy
        self._screen = screen
        self._limits = limits
        self._normalizer = MediaSettingsNormalizer(policy, screen)

    def compose(
        self,
        item: MediaItem,
        *,
        caption: str | None,
        captionmeta: dict[str, object],
        mediameta: dict[str, object],
        native: bool,
    ) -> InputMedia:
        handler = select_handler(item)
        mapping: dict[str, object] = {}

        if caption is not None:
            if len(str(caption)) > self._limits.captionlimit():
                raise CaptionOverflow()
            mapping["caption"] = caption

        mapping.update(self._screen.filter(handler, captionmeta))
        mapping.update(
            self._normalizer.prepare(
                mediameta,
                native=native,
                handler=handler,
            )
        )

        arguments = {
            "media": convert(item, policy=self._policy, native=native),
            **mapping,
        }
        return handler(**arguments)


def compose(
    item: MediaItem,
    *,
    caption: str | None,
    captionmeta: dict[str, object],
    mediameta: dict[str, object],
    policy: MediaPathPolicy,
    screen: SignatureScreen,
    limits: Limits,
    native: bool,
) -> InputMedia:
    """Compose Telegram media objects enriched with Navigator metadata."""

    composer = MediaComposer(policy=policy, screen=screen, limits=limits)
    return composer.compose(
        item,
        caption=caption,
        captionmeta=captionmeta,
        mediameta=mediameta,
        native=native,
    )


__all__ = ["MediaComposer", "compose"]

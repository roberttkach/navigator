"""Album assembly helpers for Telegram payloads."""

from __future__ import annotations

from navigator.core.entity.media import MediaItem
from navigator.core.port.limits import Limits
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.telemetry import Telemetry

from .composer import MediaComposer
from ..serializer.screen import SignatureScreen
from .telemetry import AlbumTelemetry
from .types import InputMedia
from .validation import AlbumValidator


class TelegramAlbumAssembler:
    """Assemble Telegram albums from Navigator media items."""

    def __init__(self, composer: MediaComposer, validator: AlbumValidator) -> None:
        self._composer = composer
        self._validator = validator

    def assemble(
        self,
        items: list[MediaItem],
        *,
        captionmeta: dict[str, object],
        mediameta: dict[str, object],
        native: bool,
    ) -> list[InputMedia]:
        self._validator.ensure_valid(items)

        result: list[InputMedia] = []
        for index, item in enumerate(items):
            text = item.caption if index == 0 else ""
            result.append(
                self._composer.compose(
                    item,
                    caption=text,
                    captionmeta=captionmeta,
                    mediameta=mediameta,
                    native=native,
                )
            )
        return result


def assemble(
    items: list[MediaItem],
    *,
    captionmeta: dict[str, object],
    mediameta: dict[str, object],
    policy: MediaPathPolicy,
    screen: SignatureScreen,
    limits: Limits,
    native: bool,
    telemetry: Telemetry | None = None,
) -> list[InputMedia]:
    """Compose album media structures for Telegram dispatch."""

    composer = MediaComposer(policy=policy, screen=screen, limits=limits)
    validator = AlbumValidator(limits, AlbumTelemetry(telemetry))
    assembler = TelegramAlbumAssembler(composer, validator)
    return assembler.assemble(
        items,
        captionmeta=captionmeta,
        mediameta=mediameta,
        native=native,
    )


__all__ = ["TelegramAlbumAssembler", "assemble"]

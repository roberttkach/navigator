"""Path policies and conversions for Telegram media."""

from __future__ import annotations

import re

from navigator.core.entity.media import MediaItem
from navigator.core.error import EditForbidden
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.util.path import local, remote

from .types import BufferedInputFile, FSInputFile, InputFile, URLInputFile

_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-=]{20,}$")


class TelegramMediaPolicy(MediaPathPolicy):
    """Enforce media path policies for Telegram transports."""

    def __init__(self, *, strict: bool = True) -> None:
        self._strict = strict

    def admissible(self, path: object, *, inline: bool) -> bool:
        """Return ``True`` when ``path`` may be used for inline uploads."""

        if not inline:
            return True
        if isinstance(path, URLInputFile):
            return True
        if not isinstance(path, str):
            return False
        if remote(path):
            return True
        if local(path):
            return False
        return bool(_FILE_ID_RE.match(path)) if self._strict else True

    def adapt(self, path: object, *, native: bool) -> object:
        """Return a Telegram-compatible input for ``path`` respecting flags."""

        if isinstance(path, BufferedInputFile | URLInputFile):
            return path
        if isinstance(path, FSInputFile):
            if not native:
                raise EditForbidden("inline_local_path_forbidden")
            return path
        if isinstance(path, str):
            if remote(path):
                return URLInputFile(path)
            if local(path):
                if not native:
                    raise EditForbidden("inline_local_path_forbidden")
                return FSInputFile(path)
            return path
        return path


def convert(item: MediaItem, *, policy: MediaPathPolicy, native: bool) -> InputFile:
    """Return Telegram input file representation for ``item``."""

    return policy.adapt(item.path, native=native)


__all__ = ["TelegramMediaPolicy", "convert"]

"""Prepare payload bundles for history append operations."""
from __future__ import annotations

from dataclasses import dataclass

from ..bundler import PayloadBundleSource, PayloadBundler
from ..ports import AppendHistoryUseCase


@dataclass(frozen=True)
class HistoryAppendRequest:
    """Payload bundle prepared for history append operations."""

    payloads: list[object]
    key: str | None
    root: bool

    @property
    def count(self) -> int:
        return len(self.payloads)


class HistoryPayloadAppender:
    """Prepare payload bundles and delegate execution to the use-case."""

    def __init__(self, *, appender: AppendHistoryUseCase, bundler: PayloadBundler) -> None:
        self._appender = appender
        self._bundler = bundler

    def bundle(self, source: PayloadBundleSource) -> list[object]:
        """Return bundled payloads derived from ``source``."""

        return self._bundler.bundle(source)

    def prepare(
        self,
        source: PayloadBundleSource,
        *,
        key: str | None,
        root: bool,
    ) -> HistoryAppendRequest:
        """Return a structured append request derived from ``source``."""

        payloads = self.bundle(source)
        return HistoryAppendRequest(payloads=payloads, key=key, root=root)

    async def append(self, scope, request: HistoryAppendRequest) -> None:
        """Execute the append use-case using a prepared ``request``."""

        await self._appender.execute(scope, request.payloads, request.key, root=request.root)


__all__ = ["HistoryAppendRequest", "HistoryPayloadAppender"]

"""Context builders encapsulating Telegram send orchestration data."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

from navigator.core.error import InlineUnsupported
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.service.rendering.helpers import classify
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..targeting import resolve_targets
from ..serializer import text as textkit


def _ensure_inline_supported(scope: Scope) -> None:
    if scope.inline:
        raise InlineUnsupported("inline_send_not_supported")


def _preview_options(preview: LinkPreviewCodec | None, payload: Payload) -> object | None:
    if preview is None or payload.preview is None:
        return None
    return preview.encode(payload.preview)


@dataclass(frozen=True)
class SendContext:
    """Bundle prepared data required to send a payload."""

    markup: object | None
    preview: object | None
    targets: Dict[str, object]
    reporter: "SendTelemetry"

    @classmethod
    def create(
        cls,
        *,
        codec: MarkupCodec,
        scope: Scope,
        payload: Payload,
        preview: LinkPreviewCodec | None,
        channel: TelemetryChannel,
    ) -> "SendContext":
        _ensure_inline_supported(scope)
        markup = textkit.decode(codec, payload.reply)
        preview_options = _preview_options(preview, payload)
        targets = resolve_targets(scope)
        reporter = SendTelemetry(channel, scope, payload)
        return cls(
            markup=markup,
            preview=preview_options,
            targets=targets,
            reporter=reporter,
        )


class SendTelemetry:
    """Emit structured telemetry for payload delivery outcomes."""

    def __init__(self, channel: TelemetryChannel, scope: Scope, payload: Payload) -> None:
        self._channel = channel
        self._scope = scope
        self._payload = payload

    def truncated(self, stage: str) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.TOO_LONG_TRUNCATED,
            scope=profile(self._scope),
            stage=stage,
        )

    def success(self, message_id: int, extra_len: int) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(self._scope),
            payload=classify(self._payload),
            message={"id": message_id, "extra_len": extra_len},
        )


class SendContextFactory:
    """Construct :class:`SendContext` instances from raw payload data."""

    def __init__(self, codec: MarkupCodec, preview: LinkPreviewCodec | None) -> None:
        self._codec = codec
        self._preview = preview

    def build(
        self,
        scope: Scope,
        payload: Payload,
        channel: TelemetryChannel,
    ) -> SendContext:
        return SendContext.create(
            codec=self._codec,
            scope=scope,
            payload=payload,
            preview=self._preview,
            channel=channel,
        )


__all__ = ["SendContext", "SendContextFactory", "SendTelemetry"]

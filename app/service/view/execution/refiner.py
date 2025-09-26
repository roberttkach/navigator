"""Metadata reconciliation helpers for edit execution."""

from __future__ import annotations

from dataclasses import replace

from navigator.core.error import MetadataKindMissing
from navigator.core.typing.result import GroupMeta, MediaMeta, Meta, TextMeta
from navigator.core.value.content import Payload, caption

from .models import Execution


class MetaRefiner:
    """Reconcile execution metadata with persisted message state."""

    def refine(
        self,
        execution: Execution,
        verdict,
        payload: Payload,
    ) -> Meta:
        _ = verdict
        meta = execution.result.meta
        stem = execution.stem

        if isinstance(meta, MediaMeta):
            medium = meta.medium
            if medium is None and stem and stem.media:
                medium = getattr(stem.media.type, "value", None)

            file = meta.file
            if file is None:
                path = getattr(getattr(payload, "media", None), "path", None)
                if isinstance(path, str):
                    file = path
                elif stem and stem.media and isinstance(getattr(stem.media, "path", None), str):
                    file = stem.media.path

            captioncopy = meta.caption
            if captioncopy is None:
                fresh = caption(payload)
                if fresh is not None:
                    captioncopy = fresh
                elif getattr(payload, "erase", False):
                    captioncopy = ""
                elif stem and stem.media:
                    captioncopy = stem.media.caption

            return replace(meta, medium=medium, file=file, caption=captioncopy)

        if isinstance(meta, TextMeta) and stem and stem.text is not None:
            textcopy = meta.text if meta.text is not None else stem.text
            return replace(meta, text=textcopy)

        if isinstance(meta, (GroupMeta, TextMeta, MediaMeta)):
            return meta

        raise MetadataKindMissing()


__all__ = ["MetaRefiner"]


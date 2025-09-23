import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Any

from ..view.inline import InlineStrategy
from .policy import adapt
from ...internal.policy import shield
from ...log.decorators import trace
from ...log.emit import jlog
from ....domain.entity.history import Entry, Message
from ....domain.entity.media import MediaItem
from ....domain.error import ExtraForbidden, TextOverflow, CaptionOverflow
from ....domain.error import MessageUnchanged, EditForbidden, EmptyPayload
from ....domain.port.message import MessageGateway, Result
from ....domain.service.rendering import decision
from ....domain.service.rendering.config import RenderingConfig
from ....domain.service.rendering.album import aligned
from ....domain.service.rendering.helpers import classify, match
from ....domain.util.path import remote, local
from ....domain.value.content import Payload
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenderResult:
    id: int
    extra: List[int]
    meta: dict


@dataclass(frozen=True, slots=True)
class RenderNode:
    ids: List[int]
    extras: List[List[int]]
    metas: List[dict]
    changed: bool


class ViewOrchestrator:
    def __init__(self, gateway: MessageGateway, inline: InlineStrategy, rendering: RenderingConfig):
        self._gateway = gateway
        self._inline = inline
        self._rendering = rendering

    @property
    def rendering(self) -> RenderingConfig:
        return self._rendering

    @staticmethod
    def _head(e: Any) -> Optional[Message]:
        """
        Возвращает головное сообщение:
        - Entry -> первый Message
        - Message -> сам объект
        - Иначе -> None
        """
        if e is None:
            return None
        if hasattr(e, "messages"):
            try:
                return e.messages[0] if e.messages else None
            except Exception:
                return None
        if hasattr(e, "id") and hasattr(e, "ts"):
            return e
        return None

    def _album(self, stem: Message) -> List[int]:
        return [int(stem.id)] + [int(x) for x in (stem.extras or [])]

    def _alter(self, old: MediaItem, new: MediaItem) -> bool:
        if old.type != new.type:
            return True
        priorpath = getattr(old, "path", None)
        freshpath = getattr(new, "path", None)
        same = isinstance(priorpath, str) and isinstance(freshpath, str) and priorpath == freshpath
        if not same:
            return True
        return False

    @staticmethod
    def _refine(meta: dict, stem: Optional[Message], verdict: decision.Decision, payload: Payload) -> dict:
        """
        Нормализация meta:
        - Для media: восстанавливает medium/file/caption при edit_*, когда Telegram вернул bool.
        - Для text: восстанавливает text при edit_*, когда Telegram вернул bool.
        - Очистка подписи: payload.erase -> caption == "".
        """
        m = dict(meta or {})
        kind = m.get("kind")
        if kind == "media" and stem and getattr(stem, "media", None):
            if m.get("medium") is None:
                m["medium"] = getattr(stem.media.type, "value", None)

            if m.get("file") is None:
                pth = getattr(getattr(payload, "media", None), "path", None)
                if isinstance(pth, str) and not remote(pth) and not local(pth):
                    m["file"] = pth
                elif isinstance(getattr(stem.media, "path", None), str):
                    m["file"] = stem.media.path

            if m.get("caption") is None:
                from ....domain.value.content import caption as _cap
                freshcap = _cap(payload)
                if freshcap is not None:
                    m["caption"] = freshcap
                elif (getattr(payload, "media", None) and getattr(payload.media, "caption", None) == ""):
                    m["caption"] = ""
                elif payload.erase:
                    m["caption"] = ""
                else:
                    m["caption"] = stem.media.caption
        elif kind == "text" and stem and (getattr(stem, "text", None) is not None):
            if m.get("text") is None:
                m["text"] = stem.text
        return m

    @staticmethod
    def _verify(meta: dict) -> dict:
        kind = meta.get("kind")
        if not isinstance(kind, str):
            raise ValueError("render_meta_missing_kind")
        if kind not in {"text", "media", "group"}:
            raise ValueError(f"render_meta_unsupported_kind:{kind}")
        return meta

    @trace(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
    async def swap(
            self,
            scope: Scope,
            payload: Payload,
            last: Optional[Entry | Message],
            verdict: decision.Decision,
    ) -> Optional[RenderResult]:
        shield(scope, payload)
        payload = adapt(scope, payload)

        def _head(entity):
            return self._head(entity)

        def _compose(result: Result, stem: Optional[Message]) -> RenderResult:
            raw = {
                "kind": getattr(result, "kind", None),
                "medium": getattr(result, "medium", None),
                "file": getattr(result, "file", None),
                "caption": getattr(result, "caption", None),
                "text": getattr(result, "text", None),
                "clusters": getattr(result, "clusters", None),
                "inline": getattr(result, "inline", None),
            }
            refined = self._refine(raw, stem, verdict, payload)
            return RenderResult(id=result.id, extra=result.extra, meta=self._verify(refined))

        async def _fallback(stem: Optional[Message]) -> Optional[RenderResult]:
            result = await self._gateway.send(scope, payload)
            if stem:
                targets: List[int] = [int(stem.id)]
                targets.extend(int(x) for x in (getattr(stem, "extras", []) or []))
                try:
                    await self._gateway.delete(scope, targets)
                except Exception:
                    pass
            return _compose(result, stem)

        try:
            def _media(message):
                return bool(getattr(message, "media", None))

            if (verdict is decision.Decision.DELETE_SEND) and (not scope.inline):
                stem2 = _head(last)
                if stem2 and _media(stem2) and (payload.text is not None) and (
                        not payload.media) and (not payload.group):
                    verdict = decision.Decision.EDIT_MEDIA_CAPTION
                    payload = payload.morph(media=stem2.media)

            if verdict is decision.Decision.NO_CHANGE:
                return None

            async def _resend() -> Result:
                return await self._gateway.send(scope, payload)

            async def _rewrite() -> Optional[Result]:
                message = _head(last)
                if not message:
                    return None
                return await self._gateway.rewrite(scope, message.id, payload)

            async def _recast() -> Optional[Result]:
                message = _head(last)
                if not message:
                    return None
                return await self._gateway.recast(scope, message.id, payload)

            async def _retitle() -> Optional[Result]:
                message = _head(last)
                if not message:
                    return None
                return await self._gateway.retitle(scope, message.id, payload)

            async def _remap() -> Optional[Result]:
                message = _head(last)
                if not message:
                    return None
                return await self._gateway.remap(scope, message.id, payload)

            dispatch = {
                decision.Decision.RESEND: _resend,
                decision.Decision.EDIT_TEXT: _rewrite,
                decision.Decision.EDIT_MEDIA: _recast,
                decision.Decision.EDIT_MEDIA_CAPTION: _retitle,
                decision.Decision.EDIT_MARKUP: _remap,
            }
            runner = dispatch.get(verdict)
            if not runner:
                return None
            result = await runner()
            if result is None:
                return None
        except EmptyPayload:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="empty_payload", skip=True)
            return None
        except ExtraForbidden:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="extra_validation_failed", skip=True)
            return None
        except (TextOverflow, CaptionOverflow):
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="too_long", skip=True)
            return None
        except EditForbidden:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="edit_forbidden")
            if scope.inline:
                jlog(logger, logging.INFO, LogCode.RERENDER_INLINE_NO_FALLBACK, note="inline_no_fallback", skip=True)
                return None
            stem = self._head(last)
            fallback = await _fallback(stem)
            return fallback
        except MessageUnchanged:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="not_modified")
            if scope.inline:
                jlog(logger, logging.INFO, LogCode.RERENDER_INLINE_NO_FALLBACK, note="inline_no_fallback", skip=True)
                return None
            return None

        stem = self._head(last)
        return _compose(result, stem)

    async def inline(
            self,
            scope: Scope,
            payload: Payload,
            tail: Optional[Entry | Message],
    ) -> Optional[RenderResult]:
        head = self._head(tail)
        if head is None:
            return None
        return await self._inline.handle(
            scope=scope,
            payload=payload,
            tail=head,
            swap=self.swap,
            config=self._rendering,
        )

    async def render(
            self,
            scope: Scope,
            payloads: List[Payload],
            trail: Optional[Entry],
            inline: bool,
    ) -> Optional[RenderNode]:
        fresh = [adapt(scope, p) for p in payloads]
        if inline:
            limit = len(fresh)
            if limit > 1:
                dropped = [classify(p) for p in fresh[1:]]
                jlog(
                    logger,
                    logging.INFO,
                    LogCode.INLINE_DROP_EXTRA,
                    count_dropped=limit - 1,
                    dropped=dropped,
                )
            fresh = fresh[:1]
            if fresh:
                head = fresh[0]
                if getattr(head, "group", None):
                    first = head.group[0]
                    fresh[0] = head.morph(media=first, group=None)

        def _meta(node: Message) -> dict:
            if node.group:
                return {
                    "kind": "group",
                    "clusters": [
                        {
                            "medium": item.type.value,
                            "file": item.path,
                            "caption": item.caption,
                        }
                        for item in node.group
                    ],
                    "inline": node.inline,
                }
            if node.media:
                return {
                    "kind": "media",
                    "medium": node.media.type.value,
                    "file": node.media.path,
                    "caption": node.media.caption,
                    "inline": node.inline,
                }
            return {"kind": "text", "text": node.text, "inline": node.inline}

        shield(scope, fresh[0] if fresh else Payload())
        ledger: List[Message] = list(trail.messages) if trail else []

        primary: List[int] = []
        bundles: List[List[int]] = []
        notes: List[dict] = []
        mutated = False
        origin = 0

        if (not inline) and ledger and fresh and getattr(ledger[0], "group", None) and getattr(fresh[0], "group", None):
            former = ledger[0].group or []
            latter = fresh[0].group or []
            if aligned(former, latter):
                album = self._album(ledger[0])

                formerinfo = ledger[0].extra or {}
                latterinfo = fresh[0].extra or {}

                def _excerpt(data):
                    data = data or {}
                    view = {}
                    if "mode" in data:
                        view["mode"] = data["mode"]
                    if "entities" in data:
                        view["entities"] = data["entities"]
                    return view

                def _encode(value):
                    return json.dumps(value, sort_keys=True, separators=(",", ":")) if isinstance(value, dict) else None

                retitled = (
                    (former[0].caption or "") != (latter[0].caption or "")
                    or _encode(_excerpt(formerinfo)) != _encode(_excerpt(latterinfo))
                    or bool(formerinfo.get("show_caption_above_media")) != bool(
                        latterinfo.get("show_caption_above_media"))
                )

                def _integer(value):
                    try:
                        return int(value) if value is not None else None
                    except Exception:
                        return value

                reshaped = (
                    bool(formerinfo.get("spoiler")) != bool(latterinfo.get("spoiler"))
                    or _integer(formerinfo.get("start")) != _integer(latterinfo.get("start"))
                )

                if self._rendering.thumbguard:
                    if bool(formerinfo.get("has_thumb")) != bool(latterinfo.get("thumb") is not None):
                        reshaped = True

                if retitled:
                    cap = (latter[0].caption or "")
                    caption = fresh[0].morph(media=latter[0], group=None, text=("" if cap == "" else None))
                    await self._gateway.retitle(scope, album[0], caption)
                    mutated = True
                if not match(ledger[0].markup, fresh[0].reply):
                    await self._gateway.remap(scope, album[0], fresh[0])
                    mutated = True

                def _same(a: MediaItem, b: MediaItem) -> bool:
                    return (
                        a.type == b.type
                        and isinstance(getattr(a, "path", None), str)
                        and isinstance(getattr(b, "path", None), str)
                        and getattr(a, "path") == getattr(b, "path")
                    )

                for index, pair in enumerate(zip(former, latter)):
                    past = pair[0]
                    latest = pair[1]
                    target = album[0] if index == 0 else album[index]
                    altered = self._alter(past, latest)
                    if altered or ((not altered) and reshaped and _same(past, latest)):
                        await self._gateway.recast(scope, target, fresh[0].morph(media=latest, group=None))
                        mutated = True

                def _pick(index):
                    path = getattr(latter[index], "path", None)
                    if isinstance(path, str) and not remote(path) and not local(path):
                        return path
                    return former[index].path

                clusters = [
                    {
                        "medium": item.type.value,
                        "file": _pick(index),
                        "caption": (latter[index].caption if index == 0 else ""),
                    }
                    for index, item in enumerate(latter)
                ]

                jlog(logger, logging.INFO, LogCode.ALBUM_PARTIAL_OK, count=len(album))

                primary.append(album[0])
                bundles.append(list(ledger[0].extras))
                notes.append(
                    self._verify({"kind": "group", "clusters": clusters, "inline": ledger[0].inline})
                )

                origin = 1
            else:
                jlog(logger, logging.INFO, LogCode.ALBUM_PARTIAL_FALLBACK)

        stored = len(ledger)
        incoming = len(fresh)
        limit = min(stored, incoming)

        def _adapt(message: Message):
            class _V:
                def __init__(self, message: Message):
                    self.text = message.text
                    self.media = message.media
                    self.group = message.group
                    self.reply = message.markup
                    self.extra = message.extra

            return _V(message)

        for index in range(origin, limit):
            previous = ledger[index]
            current = fresh[index]
            verdict = decision.decide(_adapt(previous), current, self._rendering)
            if verdict is decision.Decision.NO_CHANGE:
                primary.append(previous.id)
                bundles.append(list(getattr(previous, "extras", []) or []))
                notes.append(self._verify(_meta(previous)))
                continue
            if verdict in (
                    decision.Decision.EDIT_TEXT,
                    decision.Decision.EDIT_MEDIA,
                    decision.Decision.EDIT_MEDIA_CAPTION,
                    decision.Decision.EDIT_MARKUP,
            ):
                if inline:
                    result = await self.inline(scope, current, previous)
                    primary.append(result.id if result else previous.id)
                    bundles.append(list(result.extra if result else getattr(previous, "extras", []) or []))
                    record = dict(result.meta) if result else _meta(previous)
                    record = self._refine(record, previous, verdict, current)
                    notes.append(self._verify(record))
                    if result:
                        mutated = True
                else:
                    anchor = Entry(
                        state=None,
                        view=None,
                        messages=[
                            Message(
                                id=previous.id,
                                text=previous.text,
                                media=previous.media,
                                group=previous.group,
                                markup=previous.markup,
                                preview=previous.preview,
                                extra=previous.extra,
                                extras=getattr(previous, "extras", []),
                                inline=previous.inline,
                                automated=previous.automated,
                                ts=previous.ts,
                            )
                        ],
                    )
                    result = await self.swap(scope, current, anchor, verdict)
                    primary.append(result.id if result else previous.id)
                    bundles.append(list(result.extra if result else getattr(previous, "extras", []) or []))
                    note = dict(result.meta) if result else _meta(previous)
                    notes.append(self._verify(note))
                    if result:
                        mutated = True
                continue
            if verdict == decision.Decision.DELETE_SEND:
                if inline:
                    result = await self.inline(scope, current, previous)
                    primary.append(result.id if result else previous.id)
                    bundles.append(list(result.extra if result else getattr(previous, "extras", []) or []))
                    record = dict(result.meta) if result else _meta(previous)
                    record = self._refine(record, previous, verdict, current)
                    notes.append(self._verify(record))
                    if result:
                        mutated = True
                else:
                    result = await self._gateway.send(scope, current)
                    await self._gateway.delete(scope, [previous.id] + list(getattr(previous, "extras", []) or []))
                    primary.append(result.id)
                    bundles.append(list(result.extra))
                    meta = {
                        "kind": getattr(result, "kind", None),
                        "medium": getattr(result, "medium", None),
                        "file": getattr(result, "file", None),
                        "caption": getattr(result, "caption", None),
                        "text": getattr(result, "text", None),
                        "clusters": getattr(result, "clusters", None),
                        "inline": getattr(result, "inline", None),
                    }
                    notes.append(self._verify(meta))
                    mutated = True
                continue
            result = await self._gateway.send(scope, current)
            primary.append(result.id)
            bundles.append(list(result.extra))
            meta = {
                "kind": getattr(result, "kind", None),
                "medium": getattr(result, "medium", None),
                "file": getattr(result, "file", None),
                "caption": getattr(result, "caption", None),
                "text": getattr(result, "text", None),
                "clusters": getattr(result, "clusters", None),
                "inline": getattr(result, "inline", None),
            }
            notes.append(self._verify(meta))
            mutated = True

        if stored > incoming:
            targets: List[int] = []
            for message in ledger[incoming:]:
                targets.append(message.id)
                targets.extend(list(getattr(message, "extras", []) or []))
            if targets and not inline:
                await self._gateway.delete(scope, targets)
                mutated = True
        if incoming > stored:
            if not inline:
                for payload in fresh[stored:]:
                    result = await self._gateway.send(scope, payload)
                    primary.append(result.id)
                    bundles.append(list(result.extra))
                    meta = {
                        "kind": getattr(result, "kind", None),
                        "medium": getattr(result, "medium", None),
                        "file": getattr(result, "file", None),
                        "caption": getattr(result, "caption", None),
                        "text": getattr(result, "text", None),
                        "clusters": getattr(result, "clusters", None),
                        "inline": getattr(result, "inline", None),
                    }
                    notes.append(self._verify(meta))
                    mutated = True
        if not primary:
            return None
        return RenderNode(ids=primary, extras=bundles, metas=notes, changed=mutated)

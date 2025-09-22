import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Any

from ..view.inline import InlineStrategy
from .policy import adapt
from ...internal import policy as _pol
from ...internal.policy import shield
from ...log.decorators import trace
from ...log.emit import jlog
from ....domain.entity.history import Entry, Msg
from ....domain.entity.media import MediaItem
from ....domain.error import ExtraKeyForbidden, TextTooLong, CaptionTooLong
from ....domain.error import MessageNotChanged, MessageEditForbidden, EmptyPayload
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
class RenderResultNode:
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
    def _head(e: Any) -> Optional[Msg]:
        """
        Возвращает головное сообщение:
        - Entry -> первый Msg
        - Msg -> сам объект
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

    def _album(self, stem: Msg) -> List[int]:
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
    def _refine(meta: dict, stem: Optional[Msg], dec: decision.Decision, payload: Payload) -> dict:
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
            last: Optional[Entry | Msg],
            dec: decision.Decision,
    ) -> Optional[RenderResult]:
        shield(scope, payload)
        payload = adapt(scope, payload)

        def _head(e):
            return self._head(e)

        def _compose(r: Result, stem: Optional[Msg]) -> RenderResult:
            rawmeta = {
                "kind": getattr(r, "kind", None),
                "medium": getattr(r, "medium", None),
                "file": getattr(r, "file", None),
                "caption": getattr(r, "caption", None),
                "text": getattr(r, "text", None),
                "clusters": getattr(r, "clusters", None),
                "inline": getattr(r, "inline", None),
            }
            normmeta = self._refine(rawmeta, stem, dec, payload)
            return RenderResult(id=r.id, extra=r.extra, meta=self._verify(normmeta))

        async def _fallback(stem: Optional[Msg]) -> Optional[RenderResult]:
            rr = await self._gateway.send(scope, payload)
            if stem:
                targets: List[int] = [int(stem.id)]
                targets.extend(int(x) for x in (getattr(stem, "extras", []) or []))
                try:
                    await self._gateway.delete(scope, targets)
                except Exception:
                    pass
            return _compose(rr, stem)

        try:
            def _media(x):
                return bool(getattr(x, "media", None))

            if _pol.ImplicitCaption and (dec is decision.Decision.DELETE_SEND) and (not scope.inline):
                stem2 = _head(last)
                if stem2 and _media(stem2) and (payload.text is not None) and (
                        not payload.media) and (not payload.group):
                    dec = decision.Decision.EDIT_MEDIA_CAPTION
                    payload = payload.morph(media=stem2.media)

            if dec is decision.Decision.NO_CHANGE:
                return None

            async def _resend() -> Result:
                return await self._gateway.send(scope, payload)

            async def _rewrite() -> Optional[Result]:
                m = _head(last)
                if not m:
                    return None
                return await self._gateway.rewrite(scope, m.id, payload)

            async def _recast() -> Optional[Result]:
                m = _head(last)
                if not m:
                    return None
                return await self._gateway.recast(scope, m.id, payload)

            async def _retitle() -> Optional[Result]:
                m = _head(last)
                if not m:
                    return None
                return await self._gateway.retitle(scope, m.id, payload)

            async def _remap() -> Optional[Result]:
                m = _head(last)
                if not m:
                    return None
                return await self._gateway.remap(scope, m.id, payload)

            dispatch = {
                decision.Decision.RESEND: _resend,
                decision.Decision.EDIT_TEXT: _rewrite,
                decision.Decision.EDIT_MEDIA: _recast,
                decision.Decision.EDIT_MEDIA_CAPTION: _retitle,
                decision.Decision.EDIT_MARKUP: _remap,
            }
            fn = dispatch.get(dec)
            if not fn:
                return None
            result = await fn()
            if result is None:
                return None
        except EmptyPayload:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="empty_payload", skip=True)
            if _pol.StrictAbort:
                raise
            return None
        except ExtraKeyForbidden:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="extra_validation_failed", skip=True)
            if _pol.StrictAbort:
                raise
            return None
        except (TextTooLong, CaptionTooLong):
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="too_long", skip=True)
            if _pol.StrictAbort:
                raise
            return None
        except MessageEditForbidden:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="edit_forbidden")
            if scope.inline:
                jlog(logger, logging.INFO, LogCode.RERENDER_INLINE_NO_FALLBACK, note="inline_no_fallback", skip=True)
                return None
            if not _pol.ResendOnBan:
                return None
            stem = self._head(last)
            fallback = await _fallback(stem)
            return fallback
        except MessageNotChanged:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="not_modified")
            if scope.inline:
                jlog(logger, logging.INFO, LogCode.RERENDER_INLINE_NO_FALLBACK, note="inline_no_fallback", skip=True)
                return None
            if not _pol.ResendOnIdle:
                return None
            stem = self._head(last)
            fallback = await _fallback(stem)
            return fallback

        stem = self._head(last)
        return _compose(result, stem)

    async def render(
            self,
            op: str,
            scope: Scope,
            payloads: List[Payload],
            trail: Optional[Entry],
            inline: bool,
    ) -> Optional[RenderResultNode]:
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

        def _meta(node: Msg) -> dict:
            if node.group:
                return {
                    "kind": "group",
                    "clusters": [
                        {"medium": it.type.value, "file": it.path, "caption": it.caption} for it in node.group
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
        ledger: List[Msg] = list(trail.messages) if trail else []

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

                def _capslice(data):
                    data = data or {}
                    view = {}
                    if "mode" in data:
                        view["mode"] = data["mode"]
                    if "entities" in data:
                        view["entities"] = data["entities"]
                    return view

                def _canon(value):
                    return json.dumps(value, sort_keys=True, separators=(",", ":")) if isinstance(value, dict) else None

                capshift = (
                    (former[0].caption or "") != (latter[0].caption or "")
                    or _canon(_capslice(formerinfo)) != _canon(_capslice(latterinfo))
                    or bool(formerinfo.get("show_caption_above_media")) != bool(
                        latterinfo.get("show_caption_above_media"))
                )

                def _intval(value):
                    try:
                        return int(value) if value is not None else None
                    except Exception:
                        return value

                def _mediaflip(prev, cur):
                    return (
                        bool(prev.get("spoiler")) != bool(cur.get("spoiler"))
                        or _intval(prev.get("start")) != _intval(cur.get("start"))
                    )

                mediaflip = _mediaflip(formerinfo, latterinfo)

                if self._rendering.thumbguard:
                    if bool(formerinfo.get("has_thumb")) != bool(latterinfo.get("thumb") is not None):
                        mediaflip = True

                replyshift = not match(ledger[0].markup, fresh[0].reply)
                if capshift:
                    cap = (latter[0].caption or "")
                    caption = fresh[0].morph(media=latter[0], group=None, text=("" if cap == "" else None))
                    await self._gateway.retitle(scope, album[0], caption)
                    mutated = True
                if replyshift:
                    await self._gateway.remap(scope, album[0], fresh[0])
                    mutated = True

                def _same(a: MediaItem, b: MediaItem) -> bool:
                    return (
                        a.type == b.type
                        and isinstance(getattr(a, "path", None), str)
                        and isinstance(getattr(b, "path", None), str)
                        and getattr(a, "path") == getattr(b, "path")
                    )

                for i, (formerunit, latterunit) in enumerate(zip(former, latter)):
                    target = album[0] if i == 0 else album[i]
                    mediaswitch = self._alter(formerunit, latterunit)
                    extraswitch = (not mediaswitch) and mediaflip and _same(formerunit, latterunit)
                    if mediaswitch or extraswitch:
                        await self._gateway.recast(scope, target, fresh[0].morph(media=latterunit, group=None))
                        mutated = True

                def _pick(idx):
                    path = getattr(latter[idx], "path", None)
                    if isinstance(path, str) and not remote(path) and not local(path):
                        return path
                    return former[idx].path

                clusters = [
                    {
                        "medium": it.type.value,
                        "file": _pick(i),
                        "caption": (latter[i].caption if i == 0 else "")
                    }
                    for i, it in enumerate(latter)
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

        pastcount = len(ledger)
        newcount = len(fresh)
        share = min(pastcount, newcount)

        def _adapt(nm: Msg):
            class _V:
                def __init__(self, m: Msg):
                    self.text = m.text
                    self.media = m.media
                    self.group = m.group
                    self.reply = m.markup
                    self.extra = m.extra

            return _V(nm)

        for i in range(origin, share):
            prev = ledger[i]
            cur = fresh[i]
            dec = decision.decide(_adapt(prev), cur, self._rendering)
            if dec is decision.Decision.NO_CHANGE:
                primary.append(prev.id)
                bundles.append(list(getattr(prev, "extras", []) or []))
                notes.append(self._verify(_meta(prev)))
                continue
            if dec in (
                    decision.Decision.EDIT_TEXT,
                    decision.Decision.EDIT_MEDIA,
                    decision.Decision.EDIT_MEDIA_CAPTION,
                    decision.Decision.EDIT_MARKUP,
            ):
                if inline:
                    rr = await self._inline.handle(
                        scope=scope,
                        payload=cur,
                        tail=prev,
                        inline=True,
                        swap=self.swap,
                        config=self._rendering,
                    )
                    primary.append(rr.id if rr else prev.id)
                    bundles.append(list(rr.extra if rr else getattr(prev, "extras", []) or []))
                    nm = dict(rr.meta) if rr else _meta(prev)
                    nm = self._refine(nm, prev, dec, cur)
                    notes.append(self._verify(nm))
                    if rr:
                        mutated = True
                else:
                    anchor = Entry(
                        state=None,
                        view=None,
                        messages=[
                            Msg(
                                id=prev.id,
                                text=prev.text,
                                media=prev.media,
                                group=prev.group,
                                markup=prev.markup,
                                preview=prev.preview,
                                extra=prev.extra,
                                extras=getattr(prev, "extras", []),
                                inline=prev.inline,
                                automated=prev.automated,
                                ts=prev.ts,
                            )
                        ],
                    )
                    rr = await self.swap(scope, cur, anchor, dec)
                    primary.append(rr.id if rr else prev.id)
                    bundles.append(list(rr.extra if rr else getattr(prev, "extras", []) or []))
                    note = dict(rr.meta) if rr else _meta(prev)
                    notes.append(self._verify(note))
                    if rr:
                        mutated = True
                continue
            if dec == decision.Decision.DELETE_SEND:
                if inline:
                    rr = await self._inline.handle(
                        scope=scope,
                        payload=cur,
                        tail=prev,
                        inline=True,
                        swap=self.swap,
                        config=self._rendering,
                    )
                    primary.append(rr.id if rr else prev.id)
                    bundles.append(list(rr.extra if rr else getattr(prev, "extras", []) or []))
                    nm = dict(rr.meta) if rr else _meta(prev)
                    nm = self._refine(nm, prev, dec, cur)
                    notes.append(self._verify(nm))
                    if rr:
                        mutated = True
                else:
                    rr = await self._gateway.send(scope, cur)
                    await self._gateway.delete(scope, [prev.id] + list(getattr(prev, "extras", []) or []))
                    primary.append(rr.id)
                    bundles.append(list(rr.extra))
                    meta = {
                        "kind": getattr(rr, "kind", None),
                        "medium": getattr(rr, "medium", None),
                        "file": getattr(rr, "file", None),
                        "caption": getattr(rr, "caption", None),
                        "text": getattr(rr, "text", None),
                        "clusters": getattr(rr, "clusters", None),
                        "inline": getattr(rr, "inline", None),
                    }
                    notes.append(self._verify(meta))
                    mutated = True
                continue
            r = await self._gateway.send(scope, cur)
            primary.append(r.id)
            bundles.append(list(r.extra))
            meta = {
                "kind": getattr(r, "kind", None),
                "medium": getattr(r, "medium", None),
                "file": getattr(r, "file", None),
                "caption": getattr(r, "caption", None),
                "text": getattr(r, "text", None),
                "clusters": getattr(r, "clusters", None),
                "inline": getattr(r, "inline", None),
            }
            notes.append(self._verify(meta))
            mutated = True

        if pastcount > newcount:
            targets: List[int] = []
            for msg in ledger[newcount:]:
                targets.append(msg.id)
                targets.extend(list(getattr(msg, "extras", []) or []))
            if targets and not inline:
                await self._gateway.delete(scope, targets)
                mutated = True
        if newcount > pastcount:
            if not inline:
                for payload in fresh[pastcount:]:
                    r = await self._gateway.send(scope, payload)
                    primary.append(r.id)
                    bundles.append(list(r.extra))
                    meta = {
                        "kind": getattr(r, "kind", None),
                        "medium": getattr(r, "medium", None),
                        "file": getattr(r, "file", None),
                        "caption": getattr(r, "caption", None),
                        "text": getattr(r, "text", None),
                        "clusters": getattr(r, "clusters", None),
                        "inline": getattr(r, "inline", None),
                    }
                    notes.append(self._verify(meta))
                    mutated = True
        if not primary:
            return None
        return RenderResultNode(ids=primary, extras=bundles, metas=notes, changed=mutated)

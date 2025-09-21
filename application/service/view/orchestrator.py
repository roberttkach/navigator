import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Any

from ..view.inline import InlineStrategy
from .policy import payload_with_allowed_reply
from ...internal import policy as _pol
from ...internal.policy import shield
from ...log.decorators import log_io
from ...log.emit import jlog
from ....domain.entity.history import Entry, Msg
from ....domain.entity.media import MediaItem
from ....domain.error import ExtraKeyForbidden, TextTooLong, CaptionTooLong
from ....domain.error import MessageNotChanged, MessageEditForbidden, EmptyPayload
from ....domain.port.message import MessageGateway, Result
from ....domain.service.rendering import decision
from ....domain.service.rendering.config import RenderingConfig
from ....domain.service.rendering.album import album_compatible
from ....domain.service.rendering.helpers import payload_kind, reply_equal
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
    def __init__(self, gateway: MessageGateway, inline: InlineStrategy, rendering_config: RenderingConfig):
        self._gateway = gateway
        self._inline = inline
        self._rendering_config = rendering_config

    @property
    def rendering_config(self) -> RenderingConfig:
        return self._rendering_config

    @staticmethod
    def _head_msg(e: Any) -> Optional[Msg]:
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

    def _album_ids(self, base_msg: Msg) -> List[int]:
        return [int(base_msg.id)] + [int(x) for x in (base_msg.extras or [])]

    def _needs_edit_media(self, old: MediaItem, new: MediaItem) -> bool:
        if old.type != new.type:
            return True
        old_path = getattr(old, "path", None)
        new_path = getattr(new, "path", None)
        same = isinstance(old_path, str) and isinstance(new_path, str) and old_path == new_path
        if not same:
            return True
        return False

    @staticmethod
    def _normalize_meta(meta: dict, base_msg: Optional[Msg], dec: decision.Decision, payload: Payload) -> dict:
        """
        Нормализация meta:
        - Для media: восстанавливает media_type/file_id/caption при edit_*, когда Telegram вернул bool.
        - Для text: восстанавливает text при edit_*, когда Telegram вернул bool.
        - Очистка подписи: payload.erase -> caption == "".
        """
        m = dict(meta or {})
        kind = m.get("kind")
        if kind == "media" and base_msg and getattr(base_msg, "media", None):
            if m.get("media_type") is None:
                m["media_type"] = getattr(base_msg.media.type, "value", None)

            if m.get("file_id") is None:
                pth = getattr(getattr(payload, "media", None), "path", None)
                if isinstance(pth, str) and not remote(pth) and not local(pth):
                    m["file_id"] = pth
                elif isinstance(getattr(base_msg.media, "path", None), str):
                    m["file_id"] = base_msg.media.path

            if m.get("caption") is None:
                from ....domain.value.content import caption as _cap
                new_cap = _cap(payload)
                if new_cap is not None:
                    m["caption"] = new_cap
                elif (getattr(payload, "media", None) and getattr(payload.media, "caption", None) == ""):
                    m["caption"] = ""
                elif payload.erase:
                    m["caption"] = ""
                else:
                    m["caption"] = base_msg.media.caption
        elif kind == "text" and base_msg and (getattr(base_msg, "text", None) is not None):
            if m.get("text") is None:
                m["text"] = base_msg.text
        return m

    @staticmethod
    def _require_kind(meta: dict) -> dict:
        kind = meta.get("kind")
        if not isinstance(kind, str):
            raise ValueError("render_meta_missing_kind")
        if kind not in {"text", "media", "group"}:
            raise ValueError(f"render_meta_unsupported_kind:{kind}")
        return meta

    @log_io(LogCode.RENDER_START, LogCode.RENDER_OK, LogCode.RENDER_SKIP)
    async def swap(
            self,
            scope: Scope,
            payload: Payload,
            last: Optional[Entry | Msg],
            dec: decision.Decision,
    ) -> Optional[RenderResult]:
        shield(scope, payload)
        payload = payload_with_allowed_reply(scope, payload)

        def _head_msg(e):
            return self._head_msg(e)

        def _build_render_result_from_result(r: Result, base_msg: Optional[Msg]) -> RenderResult:
            raw_meta = {
                "kind": getattr(r, "kind", None),
                "media_type": getattr(r, "media_type", None),
                "file_id": getattr(r, "file_id", None),
                "caption": getattr(r, "caption", None),
                "text": getattr(r, "text", None),
                "group_items": getattr(r, "group_items", None),
                "inline": getattr(r, "inline", None),
            }
            norm_meta = self._normalize_meta(raw_meta, base_msg, dec, payload)
            return RenderResult(id=r.id, extra=r.extra, meta=self._require_kind(norm_meta))

        async def _fallback_resend_delete(base_msg: Optional[Msg]) -> Optional[RenderResult]:
            # resend + delete(base_id + aux)
            rr = await self._gateway.send(scope, payload)
            if base_msg:
                ids_to_delete: List[int] = [int(base_msg.id)]
                ids_to_delete.extend(int(x) for x in (getattr(base_msg, "extras", []) or []))
                try:
                    await self._gateway.delete(scope, ids_to_delete)
                except Exception:
                    pass
            return _build_render_result_from_result(rr, base_msg)

        try:
            # Имплицитный edit_caption по non-inline: пришёл только text при одном медиа в базе
            def _has_media_single_local(x):
                return bool(getattr(x, "media", None))

            if _pol.ImplicitCaption and (dec is decision.Decision.DELETE_SEND) and (not scope.inline):
                base_msg2 = _head_msg(last)
                if base_msg2 and _has_media_single_local(base_msg2) and (payload.text is not None) and (
                        not payload.media) and (not payload.group):
                    dec = decision.Decision.EDIT_MEDIA_CAPTION
                    payload = payload.morph(media=base_msg2.media)  # чтобы caption(payload) вычислился как text

            if dec is decision.Decision.NO_CHANGE:
                return None

            async def _resend() -> Result:
                return await self._gateway.send(scope, payload)

            async def _edit_text() -> Optional[Result]:
                m = _head_msg(last)
                if not m:
                    return None
                return await self._gateway.edit_text(scope, m.id, payload)

            async def _edit_media() -> Optional[Result]:
                m = _head_msg(last)
                if not m:
                    return None
                return await self._gateway.edit_media(scope, m.id, payload)

            async def _edit_caption() -> Optional[Result]:
                m = _head_msg(last)
                if not m:
                    return None
                return await self._gateway.edit_caption(scope, m.id, payload)

            async def _edit_markup() -> Optional[Result]:
                m = _head_msg(last)
                if not m:
                    return None
                return await self._gateway.edit_markup(scope, m.id, payload)

            dispatch = {
                decision.Decision.RESEND: _resend,
                decision.Decision.EDIT_TEXT: _edit_text,
                decision.Decision.EDIT_MEDIA: _edit_media,
                decision.Decision.EDIT_MEDIA_CAPTION: _edit_caption,
                decision.Decision.EDIT_MARKUP: _edit_markup,
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
            base_msg = self._head_msg(last)
            rr_fallback = await _fallback_resend_delete(base_msg)
            return rr_fallback
        except MessageNotChanged:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="not_modified")
            if scope.inline:
                jlog(logger, logging.INFO, LogCode.RERENDER_INLINE_NO_FALLBACK, note="inline_no_fallback", skip=True)
                return None
            if not _pol.ResendOnIdle:
                return None
            base_msg = self._head_msg(last)
            rr_fallback = await _fallback_resend_delete(base_msg)
            return rr_fallback

        base_msg = self._head_msg(last)
        return _build_render_result_from_result(result, base_msg)

    async def render_node(
            self,
            op: str,
            scope: Scope,
            payloads: List[Payload],
            last_node: Optional[Entry],
            inline: bool,
    ) -> Optional[RenderResultNode]:
        new = [payload_with_allowed_reply(scope, p) for p in payloads]
        if inline:
            original_len = len(new)
            if original_len > 1:
                dropped = [payload_kind(p) for p in new[1:]]
                jlog(
                    logger,
                    logging.INFO,
                    LogCode.INLINE_DROP_EXTRA,
                    count_dropped=original_len - 1,
                    dropped=dropped,
                )
            new = new[:1]
            if new:
                p0 = new[0]
                if getattr(p0, "group", None):
                    first = p0.group[0]
                    new[0] = p0.morph(media=first, group=None)

        def _meta_from_msg(o: Msg) -> dict:
            if o.group:
                return {
                    "kind": "group",
                    "group_items": [
                        {"media_type": it.type.value, "file_id": it.path, "caption": it.caption} for it in o.group
                    ],
                    "inline": o.inline,
                }
            if o.media:
                return {
                    "kind": "media",
                    "media_type": o.media.type.value,
                    "file_id": o.media.path,
                    "caption": o.media.caption,
                    "inline": o.inline,
                }
            return {"kind": "text", "text": o.text, "inline": o.inline}

        shield(scope, new[0] if new else Payload())
        old: List[Msg] = list(last_node.messages) if last_node else []

        # Выходные буферы доступны и для ветки альбомов
        out_ids: List[int] = []
        out_extras: List[List[int]] = []
        out_metas: List[dict] = []
        changed = False
        start_idx = 0  # сдвиг основного цикла при partial-edit альбома

        # Частичное редактирование групп (non-inline, для первого сообщения узла)
        # Правила:
        # - Используется один «глобальный» extra для всей группы. Per-item extra не поддержан по контракту DTO/истории.
        # - Подпись и её позиция изменяются только на первом элементе (edit_caption/markup по id первого сообщения).
        # - Медиа-уровень (spoiler/start/thumb*) применяется поэлементно, но только если файл не менялся,
        #   либо включён thumb_watch и задан thumb.
        # - Для metas.group_items file_id берётся из нового payload, если это уже file_id (строка и не путь/URL),
        #   иначе из истории (старый file_id). Это гарантирует консистентность истории.
        if (not inline) and old and new and getattr(old[0], "group", None) and getattr(new[0], "group", None):
            old_group = old[0].group or []
            new_group = new[0].group or []
            if album_compatible(old_group, new_group):
                ids = self._album_ids(old[0])

                # --- extra (глобально для группы) ---
                old_e = old[0].extra or {}
                new_e = new[0].extra or {}

                def _cap_extra_only(d):
                    d = d or {}
                    out = {}
                    if "mode" in d: out["mode"] = d["mode"]
                    if "entities" in d: out["entities"] = d["entities"]
                    return out

                def _canon(x):  # локальный канонизатор
                    return json.dumps(x, sort_keys=True, separators=(",", ":")) if isinstance(x, dict) else None

                caption_text_changed = ((old_group[0].caption or "") != (new_group[0].caption or ""))
                caption_entities_changed = (_canon(_cap_extra_only(old_e)) != _canon(_cap_extra_only(new_e)))
                caption_pos_changed = bool(old_e.get("show_caption_above_media")) != bool(
                    new_e.get("show_caption_above_media"))
                caption_changed = caption_text_changed or caption_entities_changed or caption_pos_changed

                def _int_or_none(v):
                    try:
                        return int(v) if v is not None else None
                    except Exception:
                        return v

                def _media_affects_changed(oe, ne):
                    return (
                            bool(oe.get("spoiler")) != bool(ne.get("spoiler"))
                            or _int_or_none(oe.get("start")) != _int_or_none(ne.get("start"))
                    )

                media_extra_changed = _media_affects_changed(old_e, new_e)

                # thumb: корректный триггер по факту снятия/добавления миниатюры
                if self._rendering_config.thumb_watch:
                    if bool(old_e.get("has_thumb")) != bool(new_e.get("thumb") is not None):
                        media_extra_changed = True

                # --- 1) подпись/клавиатура на первом сообщении ---
                reply_changed = not reply_equal(old[0].markup, new[0].reply)
                if caption_changed:
                    # Явная очистка подписи: если новая caption пустая — передаём text="".
                    cap = (new_group[0].caption or "")
                    p_for_cap = new[0].morph(media=new_group[0], group=None, text=("" if cap == "" else None))
                    await self._gateway.edit_caption(scope, ids[0], p_for_cap)
                    changed = True
                if reply_changed:
                    await self._gateway.edit_markup(scope, ids[0], new[0])
                    changed = True

                # --- 2) поэлементные edit_media (смена файла ИЛИ медиа-экстра) ---
                def _same_file(a: MediaItem, b: MediaItem) -> bool:
                    return (
                            a.type == b.type
                            and isinstance(getattr(a, "path", None), str)
                            and isinstance(getattr(b, "path", None), str)
                            and getattr(a, "path") == getattr(b, "path")
                    )

                for i, (oi, ni) in enumerate(zip(old_group, new_group)):
                    target_id = ids[0] if i == 0 else ids[i]
                    need_file_switch = self._needs_edit_media(oi, ni)
                    need_extra_switch = (not need_file_switch) and media_extra_changed and _same_file(oi, ni)
                    if need_file_switch or need_extra_switch:
                        await self._gateway.edit_media(scope, target_id, new[0].morph(media=ni, group=None))
                        changed = True

                # --- 3) meta.group_items с актуальным file_id ---
                def _pick_file_id(i):
                    p = getattr(new_group[i], "path", None)
                    if isinstance(p, str) and not remote(p) and not local(p):
                        return p  # новый file_id
                    return old_group[i].path  # старый file_id

                group_items = [
                    {
                        "media_type": it.type.value,
                        "file_id": _pick_file_id(i),
                        "caption": (new_group[i].caption if i == 0 else "")
                    }
                    for i, it in enumerate(new_group)
                ]

                jlog(logger, logging.INFO, LogCode.ALBUM_PARTIAL_OK, count=len(ids))

                # 1 логический элемент для «головы» группы
                out_ids.append(ids[0])
                out_extras.append(list(old[0].extras))
                out_metas.append(
                    self._require_kind({"kind": "group", "group_items": group_items, "inline": old[0].inline})
                )

                # продолжить обработку узла с индекса 1
                start_idx = 1
            else:
                jlog(logger, logging.INFO, LogCode.ALBUM_PARTIAL_FALLBACK)

        n_old = len(old)
        n_new = len(new)
        n_common = min(n_old, n_new)

        def _adapt(nm: Msg):
            class _V:
                def __init__(self, m: Msg):
                    self.text = m.text
                    self.media = m.media
                    self.group = m.group
                    self.reply = m.markup
                    self.extra = m.extra

            return _V(nm)

        for i in range(start_idx, n_common):
            o = old[i]
            p = new[i]
            dec = decision.decide(_adapt(o), p, self._rendering_config)
            if dec is decision.Decision.NO_CHANGE:
                out_ids.append(o.id)
                out_extras.append(list(getattr(o, "extras", []) or []))
                out_metas.append(self._require_kind(_meta_from_msg(o)))
                continue
            if dec in (
                    decision.Decision.EDIT_TEXT,
                    decision.Decision.EDIT_MEDIA,
                    decision.Decision.EDIT_MEDIA_CAPTION,
                    decision.Decision.EDIT_MARKUP,
            ):
                if inline:
                    rr = await self._inline.handle_element(
                        scope=scope,
                        payload=p,
                        last_message=o,
                        inline=True,
                        swap=self.swap,
                        rendering_config=self._rendering_config,
                    )
                    out_ids.append(rr.id if rr else o.id)
                    out_extras.append(list(rr.extra if rr else getattr(o, "extras", []) or []))
                    nm = dict(rr.meta) if rr else _meta_from_msg(o)
                    nm = self._normalize_meta(nm, o, dec, p)
                    out_metas.append(self._require_kind(nm))
                    if rr:
                        changed = True
                else:
                    dummy = Entry(
                        state=None,
                        view=None,
                        messages=[
                            Msg(
                                id=o.id,
                                text=o.text,
                                media=o.media,
                                group=o.group,
                                markup=o.markup,
                                preview=o.preview,
                                extra=o.extra,
                                extras=getattr(o, "extras", []),
                                inline=o.inline,
                                automated=o.automated,
                                ts=o.ts,
                            )
                        ],
                    )
                    rr = await self.swap(scope, p, dummy, dec)
                    out_ids.append(rr.id if rr else o.id)
                    out_extras.append(list(rr.extra if rr else getattr(o, "extras", []) or []))
                    meta_src = dict(rr.meta) if rr else _meta_from_msg(o)
                    out_metas.append(self._require_kind(meta_src))
                    if rr:
                        changed = True
                continue
            if dec == decision.Decision.DELETE_SEND:
                if inline:
                    rr = await self._inline.handle_element(
                        scope=scope,
                        payload=p,
                        last_message=o,
                        inline=True,
                        swap=self.swap,
                        rendering_config=self._rendering_config,
                    )
                    out_ids.append(rr.id if rr else o.id)
                    out_extras.append(list(rr.extra if rr else getattr(o, "extras", []) or []))
                    nm = dict(rr.meta) if rr else _meta_from_msg(o)
                    nm = self._normalize_meta(nm, o, dec, p)
                    out_metas.append(self._require_kind(nm))
                    if rr:
                        changed = True
                else:
                    rr = await self._gateway.send(scope, p)
                    await self._gateway.delete(scope, [o.id] + list(getattr(o, "extras", []) or []))
                    out_ids.append(rr.id)
                    out_extras.append(list(rr.extra))
                    meta = {
                        "kind": getattr(rr, "kind", None),
                        "media_type": getattr(rr, "media_type", None),
                        "file_id": getattr(rr, "file_id", None),
                        "caption": getattr(rr, "caption", None),
                        "text": getattr(rr, "text", None),
                        "group_items": getattr(rr, "group_items", None),
                        "inline": getattr(rr, "inline", None),
                    }
                    out_metas.append(self._require_kind(meta))
                    changed = True
                continue
            r = await self._gateway.send(scope, p)
            out_ids.append(r.id)
            out_extras.append(list(r.extra))
            meta = {
                "kind": getattr(r, "kind", None),
                "media_type": getattr(r, "media_type", None),
                "file_id": getattr(r, "file_id", None),
                "caption": getattr(r, "caption", None),
                "text": getattr(r, "text", None),
                "group_items": getattr(r, "group_items", None),
                "inline": getattr(r, "inline", None),
            }
            out_metas.append(self._require_kind(meta))
            changed = True

        if n_old > n_new:
            to_delete: List[int] = []
            for m in old[n_new:]:
                to_delete.append(m.id)
                to_delete.extend(list(getattr(m, "extras", []) or []))
            if to_delete and not inline:
                await self._gateway.delete(scope, to_delete)
                changed = True
        if n_new > n_old:
            if not inline:
                for p in new[n_old:]:
                    r = await self._gateway.send(scope, p)
                    out_ids.append(r.id)
                    out_extras.append(list(r.extra))
                    meta = {
                        "kind": getattr(r, "kind", None),
                        "media_type": getattr(r, "media_type", None),
                        "file_id": getattr(r, "file_id", None),
                        "caption": getattr(r, "caption", None),
                        "text": getattr(r, "text", None),
                        "group_items": getattr(r, "group_items", None),
                        "inline": getattr(r, "inline", None),
                    }
                    out_metas.append(self._require_kind(meta))
                    changed = True
        if not out_ids:
            return None
        return RenderResultNode(ids=out_ids, extras=out_extras, metas=out_metas, changed=changed)

from ...domain.value.message import Scope


def make_scope(event) -> Scope:
    lang_code = getattr(getattr(event, "from_user", None), "language_code", None)
    lang = (lang_code or "en").split("-")[0].lower()
    inline_id = getattr(event, "inline_message_id", None)
    if inline_id:
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        return Scope(chat=None, lang=lang, user=user_id, inline=inline_id, category=None)
    msg = event.message if hasattr(event, "message") else event
    chat_obj = getattr(msg, "chat", None)
    chat_id = getattr(chat_obj, "id", None)
    ctype_raw = getattr(chat_obj, "type", None)
    chat_kind = "group" if ctype_raw == "supergroup" else (
        ctype_raw if ctype_raw in {"private", "group", "channel"} else None)
    user_id = getattr(getattr(event, "from_user", None), "id", None)
    mid = getattr(msg, "message_id", None)
    biz = getattr(msg, "business_connection_id", None)
    direct_topic = getattr(getattr(msg, "direct_messages_topic", None), "topic_id", None)
    return Scope(
        chat=chat_id,
        lang=lang,
        user=user_id,
        id=mid,
        inline=None,
        business=biz,
        category=chat_kind,
        direct_topic_id=direct_topic,
    )

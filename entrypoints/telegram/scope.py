from navigator.core.value.message import Scope


def outline(event) -> Scope:
    source = getattr(getattr(event, "from_user", None), "language_code", None)
    language = (source or "en").split("-")[0].lower()
    inline = getattr(event, "inline_message_id", None)
    if inline:
        return Scope(chat=None, lang=language, inline=inline, category=None)
    message = event.message if hasattr(event, "message") else event
    chatinfo = getattr(message, "chat", None)
    chat = getattr(chatinfo, "id", None)
    kind = getattr(chatinfo, "type", None)
    category = "group" if kind == "supergroup" else (
        kind if kind in {"private", "group", "channel"} else None)
    direct_topic = getattr(
        getattr(message, "direct_messages_topic", None), "topic_id", None
    )
    direct_chat = bool(getattr(chatinfo, "is_direct_messages", False)) or bool(direct_topic)
    business = getattr(message, "business_connection_id", None)
    topic = getattr(message, "message_thread_id", None)
    if topic is None and direct_topic is not None:
        topic = direct_topic
    return Scope(
        chat=chat,
        lang=language,
        inline=None,
        business=business,
        category=category,
        topic=topic,
        direct=direct_chat,
    )

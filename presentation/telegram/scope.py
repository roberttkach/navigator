from ...domain.value.message import Scope


def make_scope(event) -> Scope:
    language_source = getattr(getattr(event, "from_user", None), "language_code", None)
    language = (language_source or "en").split("-")[0].lower()
    inline = getattr(event, "inline_message_id", None)
    if inline:
        user = getattr(getattr(event, "from_user", None), "id", None)
        return Scope(chat=None, lang=language, user=user, inline=inline, category=None)
    message = event.message if hasattr(event, "message") else event
    chat_data = getattr(message, "chat", None)
    chat = getattr(chat_data, "id", None)
    chat_type = getattr(chat_data, "type", None)
    category = "group" if chat_type == "supergroup" else (
        chat_type if chat_type in {"private", "group", "channel"} else None)
    user = getattr(getattr(event, "from_user", None), "id", None)
    business = getattr(message, "business_connection_id", None)
    topic = getattr(getattr(message, "direct_messages_topic", None), "topic_id", None)
    return Scope(
        chat=chat,
        lang=language,
        user=user,
        inline=None,
        business=business,
        category=category,
        topic=topic,
    )

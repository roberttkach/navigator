import pytest

from navigator.application.service.view.policy import allowed_reply, payload_with_allowed_reply
from navigator.domain.entity.markup import Markup
from navigator.domain.value.content import Payload
from navigator.domain.value.message import Scope


def make_scope(**kwargs) -> Scope:
    return Scope(chat=kwargs.pop("chat", 1), **kwargs)


def make_markup(kind: str) -> Markup:
    return Markup(kind=kind, data={})


def test_allowed_reply_none_returns_none() -> None:
    scope = make_scope()
    assert allowed_reply(scope, None) is None


def test_allowed_reply_private_accepts_reply_keyboard() -> None:
    scope = make_scope(category="private")
    markup = make_markup("ReplyKeyboardMarkup")
    assert allowed_reply(scope, markup) is markup


def test_allowed_reply_group_accepts_force_reply() -> None:
    scope = make_scope(category="group")
    markup = make_markup("ForceReply")
    assert allowed_reply(scope, markup) is markup


def test_allowed_reply_channel_rejects_custom_markup() -> None:
    scope = make_scope(category="channel")
    markup = make_markup("ReplyKeyboardMarkup")
    assert allowed_reply(scope, markup) is None


def test_allowed_reply_channel_accepts_inline_markup() -> None:
    scope = make_scope(category="channel")
    markup = make_markup("InlineKeyboardMarkup")
    assert allowed_reply(scope, markup) is markup


def test_allowed_reply_business_scope_accepts_only_inline() -> None:
    scope = make_scope(business="corp", category="private")
    inline = make_markup("InlineKeyboardMarkup")
    keyboard = make_markup("ReplyKeyboardMarkup")
    assert allowed_reply(scope, inline) is inline
    assert allowed_reply(scope, keyboard) is None


def test_payload_with_allowed_reply_keeps_payload_when_allowed() -> None:
    scope = make_scope(category="private")
    payload = Payload(text="hi", reply=make_markup("ReplyKeyboardMarkup"))
    assert payload_with_allowed_reply(scope, payload) is payload


def test_payload_with_allowed_reply_strips_disallowed_markup() -> None:
    scope = make_scope(category="channel")
    payload = Payload(text="hi", reply=make_markup("ReplyKeyboardMarkup"))
    sanitized = payload_with_allowed_reply(scope, payload)
    assert sanitized is not payload
    assert sanitized.reply is None
    assert sanitized.text == payload.text


def test_payload_with_allowed_reply_handles_none_reply() -> None:
    scope = make_scope(category="channel")
    payload = Payload(text="hi", reply=None)
    assert payload_with_allowed_reply(scope, payload) is payload


@pytest.mark.parametrize(
    "category",
    [None, "supergroup", "channel"],
)
def test_allowed_reply_default_to_inline_only(category: str | None) -> None:
    scope = make_scope(category=category)
    inline = make_markup("InlineKeyboardMarkup")
    keyboard = make_markup("ReplyKeyboardMarkup")
    assert allowed_reply(scope, inline) is inline
    assert allowed_reply(scope, keyboard) is None

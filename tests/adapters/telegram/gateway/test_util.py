import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[4]
_PARENT = _ROOT.parent
for path in (_ROOT, _PARENT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import sitecustomize  # noqa: F401

from navigator.adapters.telegram.gateway.util import _digest, extract
from navigator.domain.value.message import Scope


def test_digest_rejects_media_groups():
    grouped_message = SimpleNamespace(media_group_id="group", text="ignored")

    with pytest.raises(ValueError):
        _digest(grouped_message)


def test_digest_text_message_passthrough():
    message = SimpleNamespace(media_group_id=None, text="hello")

    assert _digest(message) == {"kind": "text", "text": "hello", "inline": None}


def test_extract_rejects_group_payload_without_result_message_id():
    scope = Scope(chat=123)
    payload = SimpleNamespace(group=[object()])

    with pytest.raises(AssertionError):
        extract(SimpleNamespace(), payload, scope)

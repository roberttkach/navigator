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

from navigator.adapters.telegram.gateway.util import _digest


def test_digest_rejects_media_groups():
    grouped_message = SimpleNamespace(media_group_id="group", text="ignored")

    with pytest.raises(ValueError):
        _digest(grouped_message)


def test_digest_text_message_passthrough():
    message = SimpleNamespace(media_group_id=None, text="hello")

    assert _digest(message) == {"kind": "text", "text": "hello", "inline": None}

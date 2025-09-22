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

from navigator.adapters.telegram.gateway import util as gateway
from navigator.domain.value.message import Scope


def digest():
    grouped = SimpleNamespace(media_group_id="group", text="ignored")

    with pytest.raises(ValueError):
        gateway._digest(grouped)

    message = SimpleNamespace(media_group_id=None, text="hello")
    assert gateway._digest(message) == {"kind": "text", "text": "hello", "inline": None}


def extract():
    scope = Scope(chat=123)
    payload = SimpleNamespace(group=[object()])

    with pytest.raises(AssertionError):
        gateway.extract(SimpleNamespace(), payload, scope)

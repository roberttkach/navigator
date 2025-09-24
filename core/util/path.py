from __future__ import annotations

import os
from urllib.parse import urlparse


def remote(s: str) -> bool:
    try:
        u = urlparse(str(s))
        return u.scheme in {"http", "https"} and bool(u.netloc)
    except Exception:
        return False


def local(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if s.startswith(("./", "../")):
        return True
    if os.path.isabs(s):
        return True
    if "/" in s or "\\" in s:
        return True
    return False

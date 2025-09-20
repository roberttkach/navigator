from __future__ import annotations

import os
from urllib.parse import urlparse


def is_http_url(s: str) -> bool:
    try:
        u = urlparse(str(s))
        return u.scheme in {"http", "https"} and bool(u.netloc)
    except Exception:
        return False


def is_local_path(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if s.startswith(("./", "../")):
        return True
    if os.path.isabs(s):
        return True
    # Явные признаки относительного пути: наличие разделителя каталога.
    if "/" in s or "\\" in s:
        return True
    return False

from __future__ import annotations

import os
import warnings
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


def is_http_url(s: str) -> bool:
    warnings.warn("is_http_url is deprecated; use remote", DeprecationWarning, stacklevel=2)
    return remote(s)


def is_local_path(s: str) -> bool:
    warnings.warn("is_local_path is deprecated; use local", DeprecationWarning, stacklevel=2)
    return local(s)

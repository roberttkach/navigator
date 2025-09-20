import sys
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_parent = _pkg_dir.parent

if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

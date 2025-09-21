import sys
from pathlib import Path

_package = Path(__file__).resolve().parent
_parent = _package.parent

if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

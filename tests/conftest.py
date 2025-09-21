import sys
from pathlib import Path

PACKAGE_ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT_PARENT))

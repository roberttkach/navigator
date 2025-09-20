from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (parent of the ``navigator`` package) is on ``sys.path``
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

"""Thiết lập import dự án khi pytest được gọi trực tiếp trên Windows."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

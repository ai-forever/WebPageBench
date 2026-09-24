#!/usr/bin/env python3
"""CLI wrapper for tests/bench/ui_variants_demo.py."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "bench"))
sys.path.insert(0, str(REPO / "lib" / "src"))

from ui_variants_demo import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

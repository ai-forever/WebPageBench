#!/usr/bin/env python3
"""CLI: verify bench configs, view_types, and optional API track creation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench_eval.bench_verify import BENCH_TESTS_DIR, build_test_configs, run_verification


def main() -> int:
    configs = build_test_configs(BENCH_TESTS_DIR)
    print(f"Merged configs: {len(configs)}")

    errors = run_verification(check_api=True)
    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(" -", e)
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

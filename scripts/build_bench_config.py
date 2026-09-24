#!/usr/bin/env python3
"""Validate tests/bench/config.json — canonical source, not generated from branded mocks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tests" / "bench" / "config.json"
KV = ROOT / "site" / "backend" / "static" / "kv"

EXPECTED_SECTIONS = ("hub", "shop", "books", "grocery", "rail", "hotels", "files")
EXPECTED_KV = {
    "shop": "shop/shop_kv.json",
    "books": "books/books_kv.json",
    "grocery": "grocery/grocery_kv.json",
    "rail": "rail/rail_kv.json",
    "hotels": "hotels/hotels_index.json",
}


def main() -> int:
    if not CONFIG.is_file():
        print("missing", CONFIG, file=sys.stderr)
        return 1
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    sections = [s.get("id") for s in data.get("bench_sections") or []]
    missing = [s for s in EXPECTED_SECTIONS if s not in sections]
    if missing:
        print("missing bench_sections:", missing, file=sys.stderr)
        return 1
    domains = data.get("domain_configs") or {}
    errors = []
    for domain, rel in EXPECTED_KV.items():
        path = (domains.get(domain) or {}).get("test_data", {}).get("kv_store_path")
        if path != rel:
            errors.append(f"{domain}: kv_store_path={path!r} expected {rel!r}")
        abs_path = KV / rel
        if not abs_path.is_file():
            errors.append(f"kv file missing: {abs_path}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK", CONFIG.relative_to(ROOT), "sections=", ",".join(sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

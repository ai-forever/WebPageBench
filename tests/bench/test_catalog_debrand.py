"""Catalog KV must not keep vendor brand tokens after anonymization."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

KV = ROOT / "site" / "backend" / "static" / "kv"
BRAND_RE = ("litres", "livelib", "samokat", "tolko-na-litres")


def _walk_strings(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_strings(value)
    elif isinstance(node, str):
        yield node


def test_released_kv_has_no_vendor_brands():
    leaks = []
    for path in (KV / "books" / "books_kv.json", KV / "grocery" / "grocery_kv.json", KV / "shop" / "shop_kv.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for text in _walk_strings(data):
            low = text.lower()
            for token in BRAND_RE:
                if token in low:
                    leaks.append(f"{path.name}: {token} in {text[:80]}")
        if path.name == "shop_kv.json":
            for item in data.values():
                if isinstance(item, dict) and str(item.get("seller") or "").lower() == "ozon":
                    leaks.append(f"{path.name}: seller=ozon")
    assert leaks == [], "\n".join(leaks[:20])

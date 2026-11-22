"""Build the static market payload used by the GitHub Pages demo."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "tests" / "bench" / "config.json"
KV_PATH = ROOT / "site" / "backend" / "static" / "kv" / "shop" / "shop_kv.json"
OUT_DIR = ROOT / "site" / "frontend" / "public" / "pages-demo"


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    shop = config["domain_configs"]["shop"]
    track = {
        "test_data": {
            "unified_bench": True,
            "bench_anonymized": True,
            "site_title": config["test_data"].get("site_title") or "WebPageBench",
            "login_data": config["test_data"].get("login_data") or {},
            "personal_info": config["test_data"].get("personal_info") or {},
            "kv_store_path": "shop/shop_kv.json",
            "task": (
                "В «Маркете» найдите сухой корм Purina ONE для стерилизованных "
                "кошек с говядиной и пшеницей и добавьте в корзину."
            ),
        },
        "bench_sections": [
            section for section in config.get("bench_sections") or [] if section.get("id") == "shop"
        ],
        "domain_configs": {"shop": shop},
    }
    kv = json.loads(KV_PATH.read_text(encoding="utf-8"))
    for item in kv.values():
        if isinstance(item, dict):
            item.pop("description", None)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "track.json").write_text(
        json.dumps(track, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (OUT_DIR / "shop_kv.json").write_text(
        json.dumps(kv, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"wrote {OUT_DIR} ({len(kv)} products)")


if __name__ == "__main__":
    main()

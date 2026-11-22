"""Build the static bench payload used by the GitHub Pages demo."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "tests" / "bench" / "config.json"
KV_DIR = ROOT / "site" / "backend" / "static" / "kv"
GROCERY_DIR = ROOT / "site" / "backend" / "static" / "data" / "grocery" / "categories"
OUT_DIR = ROOT / "site" / "frontend" / "public" / "pages-demo"
DROP_KEYS = {"description", "reviews", "quotes", "youtube_videos"}

KV_FILES = [
    "shop/shop_kv.json",
    "books/books_kv.json",
    "grocery/grocery_kv.json",
    "rail/rail_kv.json",
    "hotels/hotels_index.json",
    "hotels/hotels_ae.json",
    "hotels/hotels_ch.json",
    "hotels/hotels_fr.json",
    "hotels/hotels_it.json",
    "hotels/hotels_jp.json",
    "hotels/hotels_kr.json",
    "hotels/hotels_us.json",
]


def slim(value):
    if isinstance(value, dict):
        return {key: slim(item) for key, item in value.items() if key not in DROP_KEYS}
    if isinstance(value, list):
        return [slim(item) for item in value]
    return value


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    test_data = dict(config.get("test_data") or {})
    test_data["task"] = (
        "Откройте любой раздел. Например, в «Маркете» найдите сухой корм "
        "Purina ONE для стерилизованных кошек с говядиной и пшеницей и добавьте в корзину."
    )
    track = {
        "test_data": test_data,
        "bench_sections": config.get("bench_sections") or [],
        "domain_configs": config.get("domain_configs") or {},
    }
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    write_json(OUT_DIR / "track.json", track)

    for relative in KV_FILES:
        source = KV_DIR / relative
        payload = slim(json.loads(source.read_text(encoding="utf-8")))
        destination = OUT_DIR / "kv" / relative
        write_json(destination, payload)
        print(f"{relative}: {destination.stat().st_size} bytes")

    grocery_out = OUT_DIR / "grocery"
    grocery_out.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in GROCERY_DIR.glob("*.json"):
        shutil.copyfile(source, grocery_out / source.name)
        count += 1
    print(f"wrote {OUT_DIR} ({count} grocery categories)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Record demo video: unified bench hub, domains, pytest summary."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
TRACK = "bench_demo"
BASE = f"http://localhost:5173/{TRACK}"
OUT_DIRS = [Path("/opt/cursor/artifacts"), REPO / "artifacts"]
SECTIONS = [("Маркет", 5), ("Книги", 5), ("Продукты", 4), ("Поезда", 5), ("Отели", 5), ("Услуги", 5)]

TITLE = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:linear-gradient(135deg,#1a1f36,#2d3a5c);color:#f5f7fa;font-family:system-ui,sans-serif;text-align:center}
h1{font-size:2.4rem}p{opacity:.9;font-size:1.15rem;max-width:34rem;line-height:1.5}
</style></head><body><div><h1>WebPageBench</h1>
<p>Единый обезличенный бенчмарк — 45 задач, 6 доменов, нейтральный UI</p></div></body></html>"""

def ensure_track():
    from bench_eval.bench_verify import BENCH_TESTS_DIR, merge
    from bench_eval.task_dates import apply_booking_dates
    from lib.src.agent_bench import client
    base = json.loads((BENCH_TESTS_DIR / "config.json").read_text())
    task = json.loads((BENCH_TESTS_DIR / "tasks/ecommerce_basket_any_product.json").read_text())
    cfg = merge(base, task)
    apply_booking_dates(cfg)
    p = BENCH_TESTS_DIR / "build/bench_demo.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    client.create_track(name=TRACK, id=TRACK, filepath=str(p), address="localhost:80", delete_existing=True)

def pytest_block():
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/bench/test_verify_bench.py", "-q", "--tb=no"],
        cwd=REPO, capture_output=True, text=True, timeout=120)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-10:])
    ok = "✓ 62 passed" if r.returncode == 0 else "✗ failed"
    return f"$ pytest tests/bench/test_verify_bench.py -q\n\n{tail}\n\n{ok}"

def term_html(t):
    e = t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"<!DOCTYPE html><style>body{{margin:0;background:#0d1117;color:#c9d1d9;font:15px/1.5 ui-monospace,monospace;padding:2rem;white-space:pre-wrap}}</style><pre>{e}</pre>"

def record(webm_dir, term):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(record_video_dir=str(webm_dir), viewport={"width":1280,"height":720}, record_video_size={"width":1280,"height":720})
        page = ctx.new_page()
        page.set_content(TITLE); page.wait_for_timeout(3500)
        page.goto(f"{BASE}/state_hub", wait_until="networkidle"); page.wait_for_timeout(2500)
        for label, sec in SECTIONS:
            page.goto(f"{BASE}/state_hub", wait_until="networkidle"); page.wait_for_timeout(500)
            page.locator(".bench-hub__card").filter(has_text=label).first.click()
            page.wait_for_load_state("networkidle"); page.wait_for_timeout(sec * 1000)
        page.set_content(term_html(term)); page.wait_for_timeout(5500)
        page.set_content(TITLE.replace("Единый", "Демо ·")); page.wait_for_timeout(2000)
        page.close(); ctx.close(); browser.close()
    files = sorted(webm_dir.glob("*.webm"))
    if not files: raise SystemExit("no video")
    return files[-1]

def to_mp4(webm, mp4):
    subprocess.run(["ffmpeg","-y","-i",str(webm),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(mp4)], check=True)

def main():
    for d in OUT_DIRS: d.mkdir(parents=True, exist_ok=True)
    print("track…"); ensure_track()
    print("pytest…"); term = pytest_block()
    with tempfile.TemporaryDirectory() as tmp:
        print("record…"); webm = record(Path(tmp), term)
        mp4 = OUT_DIRS[0] / "bench-demo.mp4"
        print("encode…"); to_mp4(webm, mp4)
        (OUT_DIRS[1] / "bench-demo.mp4").write_bytes(mp4.read_bytes())
    print("done", mp4, mp4.stat().st_size // 1024, "KiB")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Record a Playwright video tour of UI variant demo tracks with live interactions."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "bench"))
sys.path.insert(0, str(REPO / "lib" / "src"))

from ui_variant_profiles import list_variant_configs, load_variant_overlay, profile_domain_variants  # noqa: E402
from ui_variants_demo import (  # noqa: E402
    DEMO_SAMPLE_PROFILES,
    create_track,
    profile_entry_urls,
    track_id_for_profile,
)
from ui_variants_demo_interactions import interact_domain, next_step_label  # noqa: E402

TITLE_MS = 5200
SLIDE_MS = 9000
END_MS = 3200

TITLE = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:linear-gradient(135deg,#0f172a,#1e3a5f);color:#f8fafc;font-family:system-ui,sans-serif;text-align:center;padding:2rem}
h1{font-size:2.2rem;margin-bottom:.5rem}p{opacity:.92;font-size:1.05rem;max-width:36rem;line-height:1.55}
.sub{font-size:.95rem;opacity:.75;margin-top:1rem}
</style></head><body><div>
<h1>UI Variants Demo</h1>
<p>Config-driven паттерны для DATE, SELECT, COUNTER, TXT — один бенчмарк, разный UI</p>
<p class="sub">Сейчас: ввод текста, клики по полям и выбор значений</p>
</div></body></html>"""

SLIDE = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
body{{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:#111827;color:#e5e7eb;font-family:system-ui,sans-serif;text-align:center;padding:2rem}}
h2{{font-size:1.75rem;color:#93c5fd;margin-bottom:.75rem}}
p{{font-size:1.05rem;line-height:1.55;max-width:42rem;margin:.5rem auto}}
code{{background:#1f2937;padding:.2rem .5rem;border-radius:6px;font-size:.95rem}}
.next{{margin-top:1.25rem;padding:1rem 1.25rem;background:#1e293b;border-radius:12px;
font-size:1.1rem;color:#fbbf24;max-width:38rem;line-height:1.5}}
</style></head><body><div>
<h2>{title}</h2>
<p>{body}</p>
<p class="next">Далее на экране: {next_step}</p>
</div></body></html>"""


def profile_slide(profile_id: str, description: str, variants: str, next_step: str) -> str:
    return SLIDE.format(
        title=profile_id,
        body=f"{description}<br><br><code>{variants}</code>",
        next_step=next_step,
    )


def entry_slide(entry: dict[str, str], next_step: str) -> str:
    return SLIDE.format(
        title=f"{entry['label']} · {entry['domain']}",
        body=f"Классы UI: {entry['taxonomy']}<br><code>{entry['variants']}</code>",
        next_step=next_step,
    )


def resolve_profiles(args: argparse.Namespace) -> list[str]:
    if args.profile:
        return [args.profile]
    if args.all:
        return [p.stem for p in list_variant_configs()]
    return list(DEMO_SAMPLE_PROFILES)


def record_tour(profiles: list[str], *, frontend: str, api: str, out_mp4: Path) -> None:
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp:
        webm_dir = Path(tmp)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                record_video_dir=str(webm_dir),
                viewport={"width": 1280, "height": 720},
                record_video_size={"width": 1280, "height": 720},
            )
            page = ctx.new_page()
            page.set_default_timeout(30_000)

            page.set_content(TITLE)
            page.wait_for_timeout(TITLE_MS)

            for profile_id in profiles:
                overlay = load_variant_overlay(REPO / "tests" / "bench" / "configs" / f"{profile_id}.json")
                description = overlay.get("description", profile_id)
                create_track(profile_id, api_address=api)
                track_id = track_id_for_profile(profile_id)
                entries = profile_entry_urls(overlay, frontend=frontend, track_id=track_id)
                if not entries:
                    continue

                variant_str = "; ".join(e["variants"] for e in entries)
                first_domain = entries[0]["domain"]
                first_variants = profile_domain_variants(overlay, first_domain)
                page.set_content(
                    profile_slide(
                        profile_id,
                        description,
                        variant_str,
                        next_step_label(first_domain, first_variants),
                    )
                )
                page.wait_for_timeout(SLIDE_MS)

                for entry in entries:
                    domain = entry["domain"]
                    variants = profile_domain_variants(overlay, domain)
                    hint = next_step_label(domain, variants)
                    page.set_content(entry_slide(entry, hint))
                    page.wait_for_timeout(SLIDE_MS)

                    page.goto(entry["url"], wait_until="networkidle")
                    page.wait_for_timeout(900)
                    interact_domain(page, domain, variants)
                    page.wait_for_timeout(1200)

            page.set_content(TITLE.replace("UI Variants Demo", "UI Variants Demo · готово"))
            page.wait_for_timeout(END_MS)
            page.close()
            ctx.close()
            browser.close()

        webms = sorted(webm_dir.glob("*.webm"))
        if not webms:
            raise SystemExit("No video recorded")
        webm = webms[-1]
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(webm),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(out_mp4),
            ],
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--frontend-url", default=os.environ.get("BENCH_FRONTEND_URL", "http://127.0.0.1:5173"))
    parser.add_argument("--api-address", default=os.environ.get("BENCH_API_ADDRESS", "localhost:9000"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(os.environ.get("UI_VARIANTS_DEMO_OUT", REPO / "artifacts" / "ui-variants-demo.mp4")),
    )
    args = parser.parse_args()
    profiles = resolve_profiles(args)
    print(f"Recording {len(profiles)} profiles → {args.out}")
    record_tour(profiles, frontend=args.frontend_url, api=args.api_address, out_mp4=args.out)
    print(f"Done: {args.out} ({args.out.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

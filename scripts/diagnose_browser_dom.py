#!/usr/bin/env python3
"""Check whether browser-use can see the WebPageBench catalog page (same stack as eval)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "lib", "src"))

from bench_eval.browser_profile import build_browser_profile  # noqa: E402
from bench_eval.browser_warmup import warmup_browser_session  # noqa: E402
from bench_eval.config import load_config  # noqa: E402
from bench_eval.preflight import (  # noqa: E402
    ensure_track,
    probe_backend_track,
    probe_frontend_assets,
    probe_frontend_track_fetch,
    read_page_health,
    resolve_bench_config_path,
)
from bench_eval.task_url import resolve_entry_url  # noqa: E402


def _expected_api_base(config) -> str:
    scheme = "https" if config.https else "http"
    return f"{scheme}://{config.api_address}/"


async def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose browser-use DOM on a bench track")
    parser.add_argument(
        "--track-id",
        default=os.getenv("EVAL_TASK_FILTER", "ecommerce_basket_any_product"),
    )
    parser.add_argument(
        "--frontend-host",
        default=os.getenv("EVAL_FRONTEND_HOST", "127.0.0.1:5173"),
    )
    parser.add_argument(
        "--config-path",
        default=None,
        help="Merged task config path (default: tests/bench/build/<track-id>.json)",
    )
    parser.add_argument(
        "--skip-create-track",
        action="store_true",
        help="Do not create/refresh track on backend (not recommended)",
    )
    args = parser.parse_args()

    config = load_config()
    track_id = args.track_id
    task_url = f"http://{args.frontend_host}/{track_id}"
    config_path = args.config_path or resolve_bench_config_path(
        track_id, mock=config.mock
    )
    entry_url = resolve_entry_url(task_url, config_path)
    api_base = _expected_api_base(config)

    track_setup: dict = {"skipped": True}
    if not args.skip_create_track:
        track_setup = ensure_track(
            track_id=track_id,
            config_path=config_path,
            api_address=config.api_address,
            https=config.https,
        )

    backend_probe = probe_backend_track(
        track_id,
        config.api_address,
        https=config.https,
    )

    from browser_use import BrowserSession

    profile = build_browser_profile(config)
    session = BrowserSession(browser_profile=profile)
    try:
        result = await warmup_browser_session(
            session,
            entry_url,
            min_elements=config.agent_warmup_min_elements,
            timeout=config.agent_warmup_timeout,
            settle_seconds=config.agent_warmup_settle_seconds,
        )
        state = await session.get_browser_state_summary(include_screenshot=False)
        page_health = await read_page_health(session)
        frontend_origin = f"http://{args.frontend_host}"
        asset_probe = await probe_frontend_assets(
            session, frontend_origin=frontend_origin
        )
        browser_api_probe = await probe_frontend_track_fetch(
            session,
            track_id=track_id,
            api_base=api_base,
        )

        payload = {
            "task_url": task_url,
            "entry_url": entry_url,
            "expected_api_base": api_base,
            "track_setup": track_setup,
            "backend_probe": backend_probe,
            "browser_api_probe": browser_api_probe,
            "warmup": result,
            "page_health": page_health,
            "asset_probe": asset_probe,
            "final_url": state.url,
            "interactive_elements": len(state.dom_state.selector_map or {}),
            "browser_executable": profile.executable_path,
            "hints": [],
        }

        if not backend_probe.get("ok"):
            payload["hints"].append(
                "Backend track/get failed. Check EVAL_API_ADDRESS/DAB_API_PORT and that "
                "site/backend is running."
            )
        if backend_probe.get("ok") and not browser_api_probe.get("has_track"):
            payload["hints"].append(
                "Backend is OK from Python, but the browser cannot fetch track/get. "
                "Rebuild frontend with export VITE_API_URL matching the backend "
                f"(expected {api_base}) before npm run build."
            )
        if page_health.get("appHtmlLen", 0) == 0:
            if asset_probe.get("dev_main_js_ok") is False:
                payload["hints"].append(
                    "Vite dev modules do not load in headless (/src/main.js failed). "
                    "Use production preview: export VITE_API_URL=... && npm run build && npm run preview"
                )
            else:
                payload["hints"].append(
                    "Vue did not mount (#app is empty). Check frontend logs and console errors."
                )
        elif page_health.get("bodyTextLen", 0) == 0 and not result.get("ready"):
            payload["hints"].append(
                "Vue mounted but catalog is blank: track config likely did not load. "
                "Fix VITE_API_URL and recreate the track."
            )

        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.get("ready") else 1
    finally:
        await session.stop()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

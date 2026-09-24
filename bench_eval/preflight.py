"""Preflight checks before browser eval / diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests

from bench_eval.dataset import build_test_configs
from bench_eval.track import create_track


def resolve_bench_config_path(track_id: str, *, mock: str = "bench") -> str:
    """Return merged build config path for a bench task, rebuilding if needed."""
    tests_dir = f"tests/{mock}"
    build_path = Path(tests_dir) / "build" / f"{track_id}.json"
    if build_path.is_file():
        return str(build_path)

    configs = build_test_configs(tests_dir)
    for path in configs:
        if Path(path).stem == track_id:
            return path

    task_path = Path(tests_dir) / "tasks" / f"{track_id}.json"
    raise FileNotFoundError(
        f"Bench config for track {track_id!r} not found. "
        f"Expected {build_path} or {task_path}."
    )


def probe_backend_track(
    track_id: str,
    api_address: str,
    *,
    https: bool = False,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Check that backend serves track config (same API the frontend uses)."""
    scheme = "https" if https else "http"
    url = f"{scheme}://{api_address}/track/get"
    try:
        response = requests.post(
            url,
            data={"track_id": track_id},
            timeout=timeout,
        )
        body: Any
        try:
            body = response.json()
        except Exception:
            body = response.text[:500]
        track = body.get("config") if isinstance(body, dict) else None
        return {
            "ok": response.ok and bool(track),
            "status_code": response.status_code,
            "url": url,
            "has_track": bool(track),
            "error": None if response.ok and track else body,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "url": url,
            "has_track": False,
            "error": str(exc),
        }


def ensure_track(
    *,
    track_id: str,
    config_path: str,
    api_address: str,
    https: bool = False,
) -> dict[str, Any]:
    """Create or refresh the WebPageBench track on the backend."""
    test_name = Path(config_path).stem
    created = create_track(
        test_name=test_name,
        track_id=track_id,
        config_path=config_path,
        api_address=api_address,
        https=https,
    )
    return {
        "track_id": track_id,
        "config_path": config_path,
        "created": created is not None,
        "backend_track_id": created,
    }


async def probe_frontend_track_fetch(
    browser_session: Any,
    *,
    track_id: str,
    api_base: str,
) -> dict[str, Any]:
    """From the browser context, try track/get against the expected API base URL."""
    cdp = await browser_session.get_or_create_cdp_session(focus=True)
    api_base = api_base if api_base.endswith("/") else f"{api_base}/"
    fetch_url = urljoin(api_base, "track/get")
    expression = f"""
(async () => {{
  const form = new FormData();
  form.append("track_id", {json.dumps(track_id)});
  try {{
    const response = await fetch({json.dumps(fetch_url)}, {{
      method: "POST",
      body: form,
    }});
    let body = null;
    try {{
      body = await response.json();
    }} catch (e) {{
      body = await response.text();
    }}
    return {{
      ok: response.ok,
      status: response.status,
      has_track: Boolean(body && body.config),
      url: {json.dumps(fetch_url)},
    }};
  }} catch (error) {{
    return {{
      ok: false,
      status: null,
      has_track: false,
      url: {json.dumps(fetch_url)},
      error: String(error),
    }};
  }}
}})()
"""
    evaluated = await cdp.cdp_client.send.Runtime.evaluate(
        params={"expression": expression, "returnByValue": True, "awaitPromise": True},
        session_id=cdp.session_id,
    )
    return evaluated.get("result", {}).get("value") or {"error": "no result"}


async def read_page_health(browser_session: Any) -> dict[str, Any]:
    """Summarize whether Vue mounted and the page has visible content."""
    cdp = await browser_session.get_or_create_cdp_session(focus=True)
    evaluated = await cdp.cdp_client.send.Runtime.evaluate(
        params={
            "expression": """({
  readyState: document.readyState,
  title: document.title,
  appHtmlLen: document.getElementById('app')?.innerHTML?.length || 0,
  bodyTextLen: document.body?.innerText?.length || 0,
})""",
            "returnByValue": True,
        },
        session_id=cdp.session_id,
    )
    return evaluated.get("result", {}).get("value") or {}


async def probe_frontend_assets(
    browser_session: Any,
    *,
    frontend_origin: str,
) -> dict[str, Any]:
    """Check whether Vite/Vue assets load in the browser (dev /src/main.js or built /assets/)."""
    cdp = await browser_session.get_or_create_cdp_session(focus=True)
    origin = frontend_origin.rstrip("/")
    expression = f"""
(async () => {{
  const targets = [
    {json.dumps(f"{origin}/src/main.js")},
    {json.dumps(f"{origin}/@vite/client")},
  ];
  const fetchStatus = {{}};
  for (const url of targets) {{
    try {{
      const response = await fetch(url);
      fetchStatus[url] = {{
        ok: response.ok,
        status: response.status,
        contentType: response.headers.get('content-type'),
      }};
    }} catch (error) {{
      fetchStatus[url] = {{ ok: false, error: String(error) }};
    }}
  }}
  const resources = performance.getEntriesByType('resource').map((entry) => ({{
    name: entry.name,
    duration: Math.round(entry.duration),
    transferSize: entry.transferSize,
  }}));
  const scripts = Array.from(document.querySelectorAll('script')).map((node) => ({{
    src: node.src || null,
    type: node.type || 'classic',
  }}));
  return {{ fetchStatus, resources, scripts }};
}})()
"""
    evaluated = await cdp.cdp_client.send.Runtime.evaluate(
        params={"expression": expression, "returnByValue": True, "awaitPromise": True},
        session_id=cdp.session_id,
    )
    result = evaluated.get("result", {}).get("value") or {}
    main_js = result.get("fetchStatus", {}).get(f"{origin}/src/main.js", {})
    result["dev_main_js_ok"] = bool(main_js.get("ok"))
    return result

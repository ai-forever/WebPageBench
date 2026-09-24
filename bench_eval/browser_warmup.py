"""Wait for the WebPageBench Vue SPA to become interactive in browser-use."""

from __future__ import annotations

import asyncio
import time
from typing import Any


async def _start_browser_session_with_heartbeat(
    browser_session: Any,
    *,
    start_timeout: float,
    heartbeat_interval: float = 10.0,
) -> None:
    start_task = asyncio.create_task(browser_session.start())
    waited = 0.0
    while True:
        done, _ = await asyncio.wait({start_task}, timeout=heartbeat_interval)
        if start_task in done:
            exc = start_task.exception()
            if exc is not None:
                raise exc
            return
        waited += heartbeat_interval
        print(
            f"[browser-warmup] still starting Chromium... {waited:.0f}s",
            flush=True,
        )
        if waited >= start_timeout:
            start_task.cancel()
            stop = getattr(browser_session, "stop", None)
            if callable(stop):
                try:
                    await stop()
                except Exception:
                    pass
            try:
                await start_task
            except asyncio.CancelledError:
                pass
            raise TimeoutError(
                f"browser_session.start() did not finish within {start_timeout:.0f}s. "
                "Run the Playwright preflight launch test or: "
                "python -m playwright install chromium --with-deps"
            )


async def warmup_browser_session(
    browser_session: Any,
    url: str,
    *,
    min_elements: int = 3,
    timeout: float = 30.0,
    poll_interval: float = 1.0,
    settle_seconds: float = 2.0,
    start_timeout: float = 120.0,
) -> dict[str, Any]:
    """
    Navigate and poll until browser-use can see interactive DOM nodes.

    browser-use profile wait fields are not applied during CDP navigation;
    this warmup is required for slow Vite/Vue pages in headless Chromium.
    """
    from browser_use.browser.events import NavigateToUrlEvent

    print(
        f"[browser-warmup] starting Chromium session (timeout={start_timeout:.0f}s)...",
        flush=True,
    )
    await _start_browser_session_with_heartbeat(
        browser_session,
        start_timeout=start_timeout,
    )
    print(f"[browser-warmup] Chromium ready, navigating to {url}", flush=True)

    event = browser_session.event_bus.dispatch(
        NavigateToUrlEvent(url=url, new_tab=False)
    )
    await event
    await event.event_result(raise_if_any=False, raise_if_none=False)

    if settle_seconds > 0:
        await asyncio.sleep(settle_seconds)

    start = time.monotonic()
    last_count = 0
    while time.monotonic() - start < timeout:
        state = await browser_session.get_browser_state_summary(
            include_screenshot=False
        )
        dom_state = state.dom_state
        root_ok = dom_state._root is not None
        representation = (dom_state.llm_representation() or "").strip()
        count = len(dom_state.selector_map or {})
        if root_ok and representation and count >= min_elements:
            return {
                "ready": True,
                "elements": count,
                "url": state.url,
                "elapsed_s": round(time.monotonic() - start, 2),
            }
        last_count = count
        await asyncio.sleep(poll_interval)

    state = await browser_session.get_browser_state_summary(include_screenshot=False)
    dom_state = state.dom_state
    return {
        "ready": False,
        "elements": len(dom_state.selector_map or {}),
        "url": state.url,
        "dom_root": dom_state._root is not None,
        "has_representation": bool((dom_state.llm_representation() or "").strip()),
        "last_count": last_count,
        "elapsed_s": round(time.monotonic() - start, 2),
    }

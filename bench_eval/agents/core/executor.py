"""Browser "computer": plays canonical actions back through Playwright.

GUI models were trained on a desktop where pyautogui moves a real cursor. The
bench is a web SPA, so the screen is the Chromium viewport and the primitives map
onto ``page.mouse`` / ``page.keyboard`` at CSS pixel coordinates. Screenshots are
taken at exactly the viewport size, which keeps model coordinates and click
coordinates in the same frame.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from bench_eval.agents.core.actions import Action, ActionType

#: pyautogui scroll units are wheel clicks; Chromium wheel deltas are CSS pixels.
SCROLL_PIXELS_PER_CLICK = 100.0

#: pyautogui / UI-TARS key names → Playwright key names.
KEY_ALIASES: dict[str, str] = {
    "ctrl": "Control",
    "control": "Control",
    "cmd": "Meta",
    "command": "Meta",
    "win": "Meta",
    "super": "Meta",
    "meta": "Meta",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "enter": "Enter",
    "return": "Enter",
    "esc": "Escape",
    "escape": "Escape",
    "tab": "Tab",
    "space": "Space",
    "backspace": "Backspace",
    "delete": "Delete",
    "del": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pgup": "PageUp",
    "pagedown": "PageDown",
    "pgdn": "PageDown",
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
    "capslock": "CapsLock",
    "printscreen": "PrintScreen",
}


def normalize_key(key: str) -> str:
    """Translate one key token into Playwright's naming."""
    token = (key or "").strip().strip("'\"")
    if not token:
        return ""
    lowered = token.lower()
    if lowered in KEY_ALIASES:
        return KEY_ALIASES[lowered]
    if lowered.startswith("f") and lowered[1:].isdigit():
        return lowered.upper()
    if len(token) == 1:
        return token
    return token.capitalize()


@dataclass
class ActionResult:
    action: Action
    ok: bool
    error: Optional[str] = None
    detail: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"action": self.action.to_dict(), "ok": self.ok}
        if self.error:
            payload["error"] = self.error
        if self.detail:
            payload["detail"] = self.detail
        return payload


class BrowserComputer:
    """Playwright-backed screen the GUI agents act on."""

    def __init__(
        self,
        *,
        width: int = 1280,
        height: int = 720,
        headless: bool = True,
        executable_path: Optional[str] = None,
        launch_args: Optional[list[str]] = None,
        downloads_dir: Optional[str] = None,
        settle_seconds: float = 0.6,
        typing_delay_ms: int = 20,
        action_timeout: float = 30.0,
    ) -> None:
        self.width = width
        self.height = height
        self.headless = headless
        self.executable_path = executable_path
        self.launch_args = list(launch_args or [])
        self.downloads_dir = downloads_dir
        self.settle_seconds = settle_seconds
        self.typing_delay_ms = typing_delay_ms
        #: Client-side deadline for one browser call. Playwright's own timeouts
        #: are enforced by the Node driver, so they never fire when the CDP pipe
        #: itself wedges — and ``page.mouse.click`` takes no timeout at all.
        #: Without this a single stuck interaction hangs the worker forever.
        self.action_timeout = action_timeout

        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    # -- lifecycle ---------------------------------------------------------

    @classmethod
    def from_eval_config(cls, config: Any, *, width: int = 1280, height: int = 720) -> "BrowserComputer":
        """Reuse the bench's Chromium discovery and container flags."""
        from bench_eval.browser_profile import chromium_launch_args, downloads_dir, find_browser_executable

        target = downloads_dir(config) if config is not None else None
        return cls(
            width=width,
            height=height,
            headless=bool(getattr(config, "agent_headless", True)),
            executable_path=find_browser_executable(config),
            launch_args=chromium_launch_args(config) if config is not None else [],
            downloads_dir=str(target) if target else None,
            settle_seconds=float(getattr(config, "agent_wait_between_actions", 0.6) or 0.6),
            action_timeout=float(getattr(config, "agent_action_timeout", 30.0) or 30.0),
        )

    async def start(self) -> "BrowserComputer":
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        launch_kwargs: dict[str, Any] = {"headless": self.headless}
        if self.executable_path:
            launch_kwargs["executable_path"] = self.executable_path
        if self.launch_args:
            launch_kwargs["args"] = self.launch_args
            launch_kwargs["chromium_sandbox"] = False
        self._browser = await self._playwright.chromium.launch(**launch_kwargs)

        context_kwargs: dict[str, Any] = {
            "viewport": {"width": self.width, "height": self.height},
            "screen": {"width": self.width, "height": self.height},
        }
        if self.downloads_dir:
            context_kwargs["accept_downloads"] = True
        self._context = await self._browser.new_context(**context_kwargs)
        self._page = await self._context.new_page()
        if self.downloads_dir:
            Path(self.downloads_dir).mkdir(parents=True, exist_ok=True)
            self._page.on("download", self._save_download)
        return self

    def _save_download(self, download: Any) -> None:
        # Files-cabinet tasks only count as passed when a file really lands on disk.
        target = Path(self.downloads_dir or ".") / download.suggested_filename
        asyncio.ensure_future(download.save_as(str(target)))

    async def close(self) -> None:
        # Teardown goes through the same wedged pipe the actions did, so it gets
        # the same deadline — otherwise a stuck page hangs the worker on cleanup.
        for closer in (self._context, self._browser):
            if closer is not None:
                try:
                    await self._bounded(closer.close(), "close")
                except Exception:  # noqa: BLE001 - teardown must not mask run errors
                    pass
        if self._playwright is not None:
            try:
                await self._bounded(self._playwright.stop(), "playwright.stop")
            except Exception:  # noqa: BLE001
                pass
        self._page = self._context = self._browser = self._playwright = None

    async def __aenter__(self) -> "BrowserComputer":
        return await self.start()

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()

    # -- observation -------------------------------------------------------

    @property
    def page(self) -> Any:
        if self._page is None:
            raise RuntimeError("BrowserComputer.start() was not awaited")
        return self._page

    @property
    def url(self) -> Optional[str]:
        try:
            return self.page.url
        except Exception:  # noqa: BLE001
            return None

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.width, self.height

    async def goto(self, url: str, *, wait_seconds: float = 2.0, timeout: float = 60.0) -> None:
        await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout * 1000)
        except Exception:  # noqa: BLE001 - SPA polling keeps the network busy
            pass
        if wait_seconds:
            await asyncio.sleep(wait_seconds)

    async def screenshot(self) -> bytes:
        return await self._bounded(self.page.screenshot(type="png"), "screenshot")

    async def _bounded(self, awaitable: Any, label: str) -> Any:
        """Run one browser call under ``action_timeout``.

        A cancelled call leaves the driver as wedged as it was, so the next one
        times out too — the task then burns through ``max_failures`` and ends,
        which is the point: one stuck element must cost a task, not the run.
        """
        if self.action_timeout <= 0:
            return await awaitable
        try:
            return await asyncio.wait_for(awaitable, timeout=self.action_timeout)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                f"{label} did not return within {self.action_timeout:.0f}s "
                "(browser or CDP connection is wedged)"
            ) from exc

    # -- action playback ---------------------------------------------------

    async def execute(self, action: Action) -> ActionResult:
        handler = getattr(self, f"_do_{action.type.value}", None)
        if handler is None:
            return ActionResult(action=action, ok=True, detail="no-op action type")
        try:
            detail = await self._bounded(handler(action), action.type.value)
        except Exception as exc:  # noqa: BLE001 - a bad coordinate must not kill the run
            return ActionResult(action=action, ok=False, error=f"{type(exc).__name__}: {exc}")
        if action.type not in {ActionType.WAIT, ActionType.NOOP}:
            await self._settle()
        return ActionResult(action=action, ok=True, detail=detail)

    async def execute_all(self, actions: list[Action]) -> list[ActionResult]:
        results: list[ActionResult] = []
        for action in actions:
            results.append(await self.execute(action))
            if action.is_terminal:
                break
        return results

    async def _settle(self) -> None:
        if self.settle_seconds > 0:
            await asyncio.sleep(self.settle_seconds)

    def _point(self, action: Action) -> tuple[float, float]:
        if action.x is None or action.y is None:
            raise ValueError(f"{action.type.value} requires coordinates")
        return (
            min(max(float(action.x), 0.0), self.width - 1.0),
            min(max(float(action.y), 0.0), self.height - 1.0),
        )

    async def _do_click(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.click(x, y)
        return f"click at ({x:.0f}, {y:.0f})"

    async def _do_double_click(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.dblclick(x, y)
        return f"double click at ({x:.0f}, {y:.0f})"

    async def _do_triple_click(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.click(x, y, click_count=3)
        return f"triple click at ({x:.0f}, {y:.0f})"

    async def _do_right_click(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.click(x, y, button="right")
        return f"right click at ({x:.0f}, {y:.0f})"

    async def _do_middle_click(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.click(x, y, button="middle")
        return f"middle click at ({x:.0f}, {y:.0f})"

    async def _do_move(self, action: Action) -> str:
        x, y = self._point(action)
        await self.page.mouse.move(x, y)
        return f"move to ({x:.0f}, {y:.0f})"

    async def _do_drag(self, action: Action) -> str:
        x, y = self._point(action)
        if action.to_x is None or action.to_y is None:
            raise ValueError("drag requires a destination")
        to_x = min(max(float(action.to_x), 0.0), self.width - 1.0)
        to_y = min(max(float(action.to_y), 0.0), self.height - 1.0)
        await self.page.mouse.move(x, y)
        await self.page.mouse.down()
        await self.page.mouse.move(to_x, to_y, steps=24)
        await self.page.mouse.up()
        return f"drag ({x:.0f}, {y:.0f}) -> ({to_x:.0f}, {to_y:.0f})"

    async def _do_type(self, action: Action) -> str:
        text = action.text or ""
        if action.x is not None and action.y is not None:
            x, y = self._point(action)
            await self.page.mouse.click(x, y)
        lines = text.split("\n")
        for index, line in enumerate(lines):
            if line:
                await self.page.keyboard.type(line, delay=self.typing_delay_ms)
            if index < len(lines) - 1:
                await self.page.keyboard.press("Enter")
        return f"typed {len(text)} chars"

    async def _do_key(self, action: Action) -> str:
        keys = [normalize_key(key) for key in action.keys if normalize_key(key)]
        if not keys:
            raise ValueError("key action without keys")
        combo = "+".join(keys)
        await self.page.keyboard.press(combo)
        return f"pressed {combo}"

    async def _do_scroll(self, action: Action) -> str:
        if action.x is not None and action.y is not None:
            x, y = self._point(action)
            await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(action.scroll_dx, action.scroll_dy)
        return f"wheel dx={action.scroll_dx:.0f} dy={action.scroll_dy:.0f}"

    async def _do_wait(self, action: Action) -> str:
        seconds = float(action.seconds or 3.0)
        await asyncio.sleep(min(seconds, 30.0))
        return f"waited {seconds:.1f}s"

    async def _do_navigate(self, action: Action) -> str:
        if not action.url:
            raise ValueError("navigate requires a url")
        await self.goto(action.url)
        return f"navigated to {action.url}"

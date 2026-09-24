"""Browser-use profile tuned for the WebPageBench Vue SPA."""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Optional

from bench_eval.config import EvalConfig

_CONTAINER_CHROMIUM_ARGS = (
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-zygote",
    "--disable-software-rasterizer",
)


def is_container_runtime() -> bool:
    """Best-effort detection of a Docker container."""
    if os.getenv("IN_DOCKER", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return Path("/.dockerenv").is_file()


def should_disable_chromium_sandbox(config: EvalConfig) -> bool:
    """Return True when headless container Chromium should launch without sandbox."""
    raw = os.getenv("AGENT_CHROMIUM_NO_SANDBOX")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return config.agent_headless and is_container_runtime()


def chromium_launch_args(config: EvalConfig) -> list[str]:
    """CLI args for headless Chromium in containers (browser-use + preflight)."""
    if not should_disable_chromium_sandbox(config):
        return []
    return list(_CONTAINER_CHROMIUM_ARGS)


def container_chromium_profile_kwargs(config: EvalConfig) -> dict:
    """Extra BrowserProfile kwargs for headless Chromium in containers."""
    if not should_disable_chromium_sandbox(config):
        return {}
    return {
        "chromium_sandbox": False,
        "args": chromium_launch_args(config),
    }


# Recent Playwright builds ship the macOS bundle as "Google Chrome for Testing.app"
# rather than "Chromium.app", so match any bundle and filter by _usable_binaries
# below; without this nothing is discovered on macOS and the download-aware
# executable choice silently falls back to whatever browser-use picks.
_MAC_BUNDLE_GLOB = "*.app/Contents/MacOS/*"


def _usable_binaries(paths: list[str]) -> list[str]:
    """Deduplicate, keeping only executables (bundles also ship Helper binaries)."""
    seen: dict[str, None] = {}
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK) and "Helper" not in path:
            seen.setdefault(path, None)
    return list(seen)


def _discover_playwright_chromium_bins(playwright_root: Path) -> tuple[list[str], list[str]]:
    root = str(playwright_root)
    full_chromium = sorted(
        glob.glob(f"{root}/chromium-*/chrome-linux*/chrome")
        + glob.glob(f"{root}/chromium-*/chrome-mac*/{_MAC_BUNDLE_GLOB}")
    )
    headless_shell = sorted(
        glob.glob(f"{root}/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell")
        + glob.glob(f"{root}/chromium_headless_shell-*/chrome-linux*/chrome")
        + glob.glob(f"{root}/chromium_headless_shell-*/chrome-mac*/{_MAC_BUNDLE_GLOB}")
    )
    return _usable_binaries(full_chromium), _usable_binaries(headless_shell)


def find_browser_executable(config: Optional[EvalConfig] = None) -> Optional[str]:
    """Prefer Playwright Chromium used by `python -m playwright install`."""
    if config and config.agent_browser_executable:
        path = Path(config.agent_browser_executable).expanduser()
        if path.is_file():
            return str(path)

    for env_name in ("AGENT_BROWSER_EXECUTABLE", "BROWSER_EXECUTABLE_PATH"):
        raw = os.getenv(env_name)
        if raw:
            path = Path(raw).expanduser()
            if path.is_file():
                return str(path)

    playwright_root = Path(
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "~/.cache/ms-playwright")
    ).expanduser()
    full_chromium, headless_shell = _discover_playwright_chromium_bins(playwright_root)
    # chrome-headless-shell ships without a download manager, so tasks that must
    # save a file (Файлы → PDF/CSV) need full Chromium even when headless.
    prefer_headless_shell = (config.agent_headless if config else True) and not (
        config.agent_downloads_enabled if config else False
    )
    if prefer_headless_shell and headless_shell:
        return headless_shell[-1]
    if full_chromium:
        return full_chromium[-1]
    if headless_shell:
        return headless_shell[-1]
    return None


def downloads_dir(config: EvalConfig) -> Optional[Path]:
    """Directory the agent's browser saves files into (None when disabled)."""
    if not config.agent_downloads_enabled:
        return None
    raw = config.agent_downloads_dir
    if raw:
        path = Path(raw).expanduser()
    elif config.eval_output_dir:
        path = Path(config.eval_output_dir) / "downloads"
    else:
        path = Path(config.eval_results_base_dir) / "downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_browser_profile(config: EvalConfig):
    """Create a BrowserProfile with SPA-friendly timings for bench evals."""
    from browser_use import BrowserProfile
    from browser_use.browser.profile import ViewportSize

    kwargs: dict = {
        "headless": config.agent_headless,
        "minimum_wait_page_load_time": config.agent_page_load_wait,
        "wait_for_network_idle_page_load_time": config.agent_network_idle_wait,
        "wait_between_actions": config.agent_wait_between_actions,
        "window_size": ViewportSize(width=1280, height=720),
    }
    target = downloads_dir(config)
    if target is not None:
        kwargs["accept_downloads"] = True
        kwargs["downloads_path"] = str(target)
    kwargs.update(container_chromium_profile_kwargs(config))
    executable = find_browser_executable(config)
    if executable:
        kwargs["executable_path"] = executable
    return BrowserProfile(**kwargs)


def openhands_browser_tool_params(config: EvalConfig) -> dict:
    """Shared Chromium settings for OpenHands BrowserToolSet."""
    params: dict = {
        "headless": config.agent_headless,
        "action_timeout_seconds": max(float(config.agent_warmup_timeout), 60.0),
    }
    executable = find_browser_executable(config)
    if executable:
        params["executable_path"] = executable
    params.update(container_chromium_profile_kwargs(config))
    return params

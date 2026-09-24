"""Ensure @playwright/mcp browser binaries exist for the deepagents harness."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from bench_eval.browser_profile import chromium_launch_args, find_browser_executable
from bench_eval.config import load_config
from bench_eval.node_bin import node_path_env, resolve_npx_command
from bench_eval.playwright_runtime import (
    configure_playwright_env,
    repo_root_from_env,
    resolve_playwright_browsers_path,
)

_DEFAULT_MCP_BROWSER = "chrome-for-testing"
_MCP_PACKAGE = "@playwright/mcp@latest"


def _env_truthy(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def default_mcp_browser_channel() -> str:
    raw = os.getenv("PLAYWRIGHT_MCP_BROWSER_CHANNEL", "").strip()
    return raw or _DEFAULT_MCP_BROWSER


def resolve_playwright_mcp_executable(
    *,
    browsers_path: Path | None = None,
) -> str | None:
    """Return Playwright-managed Chromium binary for MCP (same cache as browser-use)."""
    repo = repo_root_from_env()
    configure_playwright_env(repo)
    if browsers_path is not None:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
    explicit = os.getenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit
    return find_browser_executable(load_config())


def mcp_browser_installed(browsers_path: Path | None = None) -> bool:
    """Return True when a launchable Chromium binary exists under PLAYWRIGHT_BROWSERS_PATH."""
    return resolve_playwright_mcp_executable(browsers_path=browsers_path) is not None


def mcp_chromium_launch_smoke(
    executable: str,
    *,
    timeout_s: float = 45.0,
) -> tuple[bool, str]:
    """Launch MCP Chromium once to catch missing OS deps before eval."""
    cfg = load_config()
    cmd = [
        executable,
        "--headless=new",
        *chromium_launch_args(cfg),
        "--disable-extensions",
        "--dump-dom",
        "about:blank",
    ]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout_s:.0f}s"
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        return False, stderr or stdout or f"exit code {exc.returncode}"

    if not completed.stdout.strip():
        return False, "empty stdout from --dump-dom"
    return True, ""


def install_playwright_mcp_browser(
    *,
    npx_command: str | None = None,
    browsers_path: Path | None = None,
    browser_channel: str | None = None,
    timeout_seconds: float = 600.0,
) -> None:
    """Download the browser bundle expected by @playwright/mcp."""
    npx = npx_command or resolve_npx_command()
    if not npx:
        raise SystemExit(
            "Playwright MCP preflight requires npx. "
            "Run ./scripts/install_nodejs.sh or set PLAYWRIGHT_MCP_COMMAND."
        )

    repo = repo_root_from_env()
    configure_playwright_env(repo)
    path = browsers_path or resolve_playwright_browsers_path(repo)
    path.mkdir(parents=True, exist_ok=True)
    channel = browser_channel or default_mcp_browser_channel()

    env = node_path_env()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(path)
    env.setdefault("PLAYWRIGHT_INSTALL_WITH_DEPS", "0")

    cmd = [npx, "-y", _MCP_PACKAGE, "install-browser", channel]
    print(
        f"[playwright-mcp-preflight] installing MCP browser channel={channel!r} "
        f"PLAYWRIGHT_BROWSERS_PATH={path}",
        flush=True,
    )
    completed = subprocess.run(
        cmd,
        check=False,
        env=env,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"Playwright MCP install-browser {channel!r} failed "
            f"(exit {completed.returncode}). "
            f"Command: {' '.join(cmd)}"
        )


def verify_playwright_mcp_launch(
    *,
    browsers_path: Path | None = None,
    timeout_s: float = 45.0,
) -> str:
    """Ensure MCP Chromium exists and launches; return executable path."""
    executable = resolve_playwright_mcp_executable(browsers_path=browsers_path)
    if not executable:
        raise SystemExit(
            "Playwright MCP Chromium executable not found under PLAYWRIGHT_BROWSERS_PATH."
        )

    if _env_truthy("SKIP_PLAYWRIGHT_MCP_LAUNCH_TEST"):
        print(
            f"[playwright-mcp-preflight] SKIP_PLAYWRIGHT_MCP_LAUNCH_TEST=1; "
            f"using {executable}",
            flush=True,
        )
        return executable

    print(
        f"[playwright-mcp-preflight] MCP Chromium launch smoke test "
        f"(timeout={timeout_s:.0f}s)...",
        flush=True,
    )
    ok, detail = mcp_chromium_launch_smoke(executable, timeout_s=timeout_s)
    if not ok:
        raise SystemExit(
            "Playwright MCP Chromium launch smoke test failed: "
            f"{detail}\nExecutable: {executable}"
        )
    print("[playwright-mcp-preflight] MCP Chromium launch smoke test OK", flush=True)
    return executable


def ensure_playwright_mcp_browser(
    *,
    npx_command: str | None = None,
    browsers_path: Path | None = None,
    browser_channel: str | None = None,
    timeout_seconds: float = 600.0,
    launch_timeout_s: float = 45.0,
) -> str:
    """Install MCP browser when missing, verify launch; return executable path."""
    repo = repo_root_from_env()
    configure_playwright_env(repo)
    path = browsers_path or resolve_playwright_browsers_path(repo)

    if _env_truthy("SKIP_PLAYWRIGHT_MCP_INSTALL"):
        if not mcp_browser_installed(path):
            raise SystemExit(
                "SKIP_PLAYWRIGHT_MCP_INSTALL=1 but Playwright MCP browser is missing under "
                f"{path}. Run: npx -y @playwright/mcp@latest install-browser "
                f"{default_mcp_browser_channel()}"
            )
        print(
            f"[playwright-mcp-preflight] SKIP_PLAYWRIGHT_MCP_INSTALL=1; "
            f"using existing browser under {path}",
            flush=True,
        )
    elif mcp_browser_installed(path) and not _env_truthy("FORCE_PLAYWRIGHT_MCP_INSTALL"):
        print(
            f"[playwright-mcp-preflight] MCP browser already present under {path}",
            flush=True,
        )
    else:
        install_playwright_mcp_browser(
            npx_command=npx_command,
            browsers_path=path,
            browser_channel=browser_channel,
            timeout_seconds=timeout_seconds,
        )
        if not mcp_browser_installed(path):
            raise SystemExit(
                f"Playwright MCP browser still missing under {path} after install-browser."
            )
        print(f"[playwright-mcp-preflight] MCP browser ready under {path}", flush=True)

    executable = verify_playwright_mcp_launch(
        browsers_path=path,
        timeout_s=launch_timeout_s,
    )
    os.environ["PLAYWRIGHT_MCP_EXECUTABLE_PATH"] = executable
    print(f"[playwright-mcp-preflight] PLAYWRIGHT_MCP_EXECUTABLE_PATH={executable}", flush=True)
    return executable


def main(argv: list[str] | None = None) -> int:
    parser = __import__("argparse").ArgumentParser(
        description="Install and verify @playwright/mcp browser for deepagents eval",
    )
    parser.add_argument(
        "--browser-channel",
        default=None,
        help=f"MCP browser channel (default: {_DEFAULT_MCP_BROWSER})",
    )
    parser.add_argument(
        "--npx",
        default=None,
        help="Path to npx (default: resolve from env)",
    )
    parser.add_argument(
        "--launch-test",
        action="store_true",
        help="Only verify MCP Chromium launch (skip install)",
    )
    args = parser.parse_args(argv)
    if args.launch_test:
        verify_playwright_mcp_launch()
    else:
        ensure_playwright_mcp_browser(
            npx_command=args.npx,
            browser_channel=args.browser_channel,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

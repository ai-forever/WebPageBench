"""Preflight checks before local browser-use evaluation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from bench_eval.browser_profile import (
    chromium_launch_args,
    find_browser_executable,
)
from bench_eval.config import EvalConfig, load_config
from bench_eval.playwright_runtime import (
    configure_playwright_env,
    install_vendor_conda_libs,
)

_INSTALL_HINT = (
    "Playwright Chromium not found.\n"
    "One-time local setup (no sudo — uses conda libs under .cache/):\n"
    "  cd $AGENT_BENCH_ROOT && ./scripts/install_playwright_chromium.sh\n"
    "Then rerun the evaluation."
)

_LAUNCH_FAIL_HINT = (
    "Chromium failed to start (missing shared libraries?).\n"
    "No sudo: ./scripts/install_playwright_chromium.sh  (conda vendor libs in .cache/)\n"
    "With sudo: PLAYWRIGHT_INSTALL_WITH_DEPS=1 ./scripts/install_playwright_chromium.sh"
)


def _env_truthy(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _missing_shared_library(detail: str) -> bool:
    lowered = detail.lower()
    return (
        "error while loading shared libraries" in lowered
        or "cannot open shared object file" in lowered
        or "libnspr" in lowered
        or "libnss" in lowered
        or "libatk" in lowered
        or "libgbm" in lowered
    )


def verify_playwright_chromium(config: EvalConfig | None = None) -> str:
    """Return Chromium executable path or exit with install instructions."""
    cfg = config or load_config()
    executable = find_browser_executable(cfg)
    if executable:
        return executable
    raise SystemExit(_INSTALL_HINT)


def install_playwright_system_deps() -> bool:
    """Install Playwright OS packages (apt). Returns True when the command succeeded."""
    print(
        "[playwright-preflight] running: python -m playwright install-deps chromium",
        flush=True,
    )
    completed = subprocess.run(
        [sys.executable, "-m", "playwright", "install-deps", "chromium"],
        check=False,
    )
    if completed.returncode == 0:
        print("[playwright-preflight] install-deps finished OK", flush=True)
        return True
    print(
        f"[playwright-preflight] install-deps exited {completed.returncode} "
        "(may need root/sudo on the image)",
        flush=True,
    )
    return False


def _prepare_chromium_runtime(config: EvalConfig) -> None:
    configure_playwright_env()


def _chromium_launch_smoke(
    config: EvalConfig,
    *,
    timeout_s: float,
) -> tuple[bool, str, str]:
    """Return (ok, detail, executable_path)."""
    _prepare_chromium_runtime(config)
    executable = find_browser_executable(config)
    if not executable:
        return False, "Chromium executable not found", ""

    cmd = [
        executable,
        "--headless=new",
        *chromium_launch_args(config),
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
        return False, f"timed out after {timeout_s:.0f}s", executable
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or f"exit code {exc.returncode}"
        return False, detail, executable

    if not completed.stdout.strip():
        return False, "empty stdout from --dump-dom", executable
    return True, "", executable


def verify_chromium_launch(
    config: EvalConfig | None = None,
    *,
    timeout_s: float = 45.0,
    auto_install_deps: bool = True,
) -> str:
    """Launch Chromium once via subprocess to catch missing OS deps early."""
    cfg = config or load_config()
    verify_playwright_chromium(cfg)

    print(
        f"[playwright-preflight] Chromium launch smoke test (timeout={timeout_s:.0f}s)...",
        flush=True,
    )
    ok, detail, executable = _chromium_launch_smoke(cfg, timeout_s=timeout_s)
    if ok:
        print("[playwright-preflight] Chromium launch smoke test OK", flush=True)
        return executable

    if (
        auto_install_deps
        and _missing_shared_library(detail)
        and not _env_truthy("SKIP_PLAYWRIGHT_INSTALL_DEPS")
    ):
        print(
            f"[playwright-preflight] launch failed ({detail}); trying conda vendor libs...",
            flush=True,
        )
        if install_vendor_conda_libs():
            ok, detail, executable = _chromium_launch_smoke(cfg, timeout_s=timeout_s)
            if ok:
                print(
                    "[playwright-preflight] Chromium launch OK (after conda vendor libs)",
                    flush=True,
                )
                return executable

        print(
            f"[playwright-preflight] trying playwright install-deps (needs sudo)...",
            flush=True,
        )
        if install_playwright_system_deps():
            ok, detail, executable = _chromium_launch_smoke(cfg, timeout_s=timeout_s)
            if ok:
                print(
                    "[playwright-preflight] Chromium launch smoke test OK (after install-deps)",
                    flush=True,
                )
                return executable

    raise SystemExit(
        f"Chromium launch smoke test failed: {detail}\n{_LAUNCH_FAIL_HINT}"
    )


def ensure_playwright_chromium(
    config: EvalConfig | None = None,
    *,
    install: bool = False,
) -> str:
    """Return Chromium path, optionally running ``playwright install chromium``."""
    cfg = config or load_config()
    executable = find_browser_executable(cfg)
    if executable:
        return executable
    if not install:
        raise SystemExit(_INSTALL_HINT)

    configure_playwright_env()
    install_cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    if _env_truthy("PLAYWRIGHT_INSTALL_WITH_DEPS"):
        install_cmd.append("--with-deps")
    print(
        "Playwright Chromium not found; running: "
        + " ".join(install_cmd),
        flush=True,
    )
    subprocess.run(install_cmd, check=True)
    executable = find_browser_executable(cfg)
    if executable:
        return executable
    raise SystemExit(
        f"{_INSTALL_HINT}\n"
        "Auto-install finished but Chromium is still missing "
        f"(PLAYWRIGHT_BROWSERS_PATH={os.environ.get('PLAYWRIGHT_BROWSERS_PATH')})."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Download Chromium into PLAYWRIGHT_BROWSERS_PATH when missing",
    )
    parser.add_argument(
        "--launch-test",
        action="store_true",
        help="Run a headless Chromium subprocess smoke test before eval",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Run playwright install-deps chromium and exit",
    )
    args = parser.parse_args()
    cfg = load_config()

    if args.install_deps:
        if not install_playwright_system_deps():
            raise SystemExit(1)
        return

    if args.install:
        path = ensure_playwright_chromium(cfg, install=True)
    else:
        path = verify_playwright_chromium(cfg)
    print(f"Playwright Chromium OK: {path}", flush=True)
    if args.launch_test:
        verify_chromium_launch(cfg)


if __name__ == "__main__":
    main()

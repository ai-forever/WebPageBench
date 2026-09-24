"""Chromium runtime paths without system sudo (conda vendor libs + LD_LIBRARY_PATH)."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Playwright Chromium deps mapped to conda-forge (no sudo). Keep names aligned with
# https://anaconda.org/conda-forge — not Debian package names like atk-2.36.
_CONDA_FORGE_PACKAGES = (
    "nspr",
    "nss",
    "atk",
    "at-spi2-atk",
    "pango",
    "cairo",
    "glib",
    "xorg-libxcomposite",
    "xorg-libxdamage",
    "xorg-libxfixes",
    "xorg-libxrandr",
    "xorg-libx11",
    "libxcb",
    "xorg-libxext",
    "libxkbcommon",
    "libdrm",
    "libgbm",
    "alsa-lib",
    "dbus",
    "libcups",
    "expat",
)


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def repo_root_from_env() -> Path:
    raw = os.getenv("AGENT_BENCH_ROOT")
    if raw:
        path = Path(raw).expanduser()
        if path.is_dir():
            return path
    return Path(__file__).resolve().parents[1]


def default_playwright_browsers_path(root: Path | None = None) -> Path:
    repo = root or repo_root_from_env()
    return repo / ".cache" / "ms-playwright"


def vendor_conda_lib_dir(root: Path | None = None) -> Path:
    repo = root or repo_root_from_env()
    return repo / ".cache" / "playwright-conda-libs"


def resolve_playwright_browsers_path(root: Path | None = None) -> Path:
    """Return a sane PLAYWRIGHT_BROWSERS_PATH (ignore empty AGENT_BENCH_ROOT exports)."""
    raw = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if raw and raw not in {"/.cache/ms-playwright", "/.cache"} and not raw.startswith("/.cache/"):
        path = Path(raw).expanduser()
        if str(path) != "/.cache":
            return path
    return default_playwright_browsers_path(root)


def conda_prefixes() -> list[Path]:
    prefixes: list[Path] = []
    for name in ("CONDA_PREFIX", "MAMBA_ROOT_PREFIX"):
        raw = os.getenv(name)
        if not raw:
            continue
        path = Path(raw).expanduser()
        if path.is_dir() and path not in prefixes:
            prefixes.append(path)
    return prefixes


def library_dirs(prefixes: list[Path]) -> list[str]:
    dirs: list[str] = []
    for prefix in prefixes:
        lib = prefix / "lib"
        if lib.is_dir():
            dirs.append(str(lib))
    return dirs


def configure_chromium_library_path(root: Path | None = None) -> str:
    """
    Prepend conda / vendor lib directories to LD_LIBRARY_PATH.

    This mirrors local Jupyter where Chromium works because conda (base) provides
    libnspr4.so without apt/sudo.
    """
    prefixes = list(conda_prefixes())
    vendor = vendor_conda_lib_dir(root)
    if vendor.is_dir():
        prefixes.insert(0, vendor)

    extra = library_dirs(prefixes)
    if not extra:
        return os.environ.get("LD_LIBRARY_PATH", "")

    current = os.environ.get("LD_LIBRARY_PATH", "")
    merged: list[str] = []
    for entry in extra + ([current] if current else []):
        if entry and entry not in merged:
            merged.append(entry)
    joined = ":".join(merged)
    os.environ["LD_LIBRARY_PATH"] = joined
    return joined


def vendor_lib_ready(root: Path | None = None) -> bool:
    lib_dir = vendor_conda_lib_dir(root) / "lib"
    if not lib_dir.is_dir():
        return False
    return any(lib_dir.glob("libnspr4.so*"))


_STUB_HOMES = frozenset({Path("/home/user")})


def _safe_home(root: Path | None = None) -> str:
    """Playwright defaults to ~/.cache; empty HOME becomes /.cache and fails."""
    repo = root or repo_root_from_env()
    fallback = str(repo)
    home = os.environ.get("HOME", "").strip()
    if not home or home in {"/", ""}:
        os.environ["HOME"] = fallback
        return fallback

    # Some containers export HOME=/home/user without a real ~/.cache; use repo root
    # so Playwright/Ouroboros do not fall back to an unwritable cache.
    try:
        home_path = Path(home).expanduser().resolve()
        if home_path in _STUB_HOMES:
            os.environ["HOME"] = fallback
            return fallback
    except OSError:
        pass

    return home


def configure_playwright_env(root: Path | None = None) -> dict[str, str]:
    """Set browser cache path, library path, and a safe HOME for Playwright CLI."""
    repo = root or repo_root_from_env()
    browsers = resolve_playwright_browsers_path(repo)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers)
    browsers.mkdir(parents=True, exist_ok=True)
    _safe_home(repo)
    configure_chromium_library_path(repo)
    return {
        "PLAYWRIGHT_BROWSERS_PATH": str(browsers),
        "HOME": os.environ["HOME"],
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
    }


def install_vendor_conda_libs(root: Path | None = None) -> bool:
    """Install Chromium OS libs into repo-local conda prefix (no sudo)."""
    conda = shutil.which("conda")
    if not conda:
        _log("[playwright-runtime] conda not found; cannot vendor OS libs without sudo")
        return False

    repo = root or repo_root_from_env()
    prefix = vendor_conda_lib_dir(repo)
    prefix.parent.mkdir(parents=True, exist_ok=True)

    if vendor_lib_ready(repo):
        configure_chromium_library_path(repo)
        return True

    base_cmd = [conda, "-y", "-p", str(prefix), "-c", "conda-forge"]
    if (prefix / "conda-meta").is_dir():
        cmd = [*base_cmd[:1], "install", *base_cmd[1:], *_CONDA_FORGE_PACKAGES]
    else:
        # conda install -p requires an existing env; create prefix on first run.
        cmd = [*base_cmd[:1], "create", *base_cmd[1:], *_CONDA_FORGE_PACKAGES]
    _log("[playwright-runtime] installing browser libs via conda: " + " ".join(cmd))
    completed = subprocess.run(
        cmd,
        check=False,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if completed.returncode != 0:
        _log(f"[playwright-runtime] conda exited {completed.returncode}")
        return False
    configure_chromium_library_path(repo)
    return vendor_lib_ready(repo)


def ensure_chromium_runtime(root: Path | None = None, *, install_vendor_libs: bool = False) -> str:
    """Configure paths and optionally create vendor conda libs under the repo."""
    repo = root or repo_root_from_env()
    configure_playwright_env(repo)
    if install_vendor_libs and not vendor_lib_ready(repo):
        install_vendor_conda_libs(repo)
    return os.environ.get("LD_LIBRARY_PATH", "")


def shell_export_lines(root: Path | None = None, *, install_vendor_libs: bool = False) -> list[str]:
    """Bash ``export`` lines for install scripts (subprocess env does not persist)."""
    repo = root or repo_root_from_env()
    ensure_chromium_runtime(repo, install_vendor_libs=install_vendor_libs)
    lines = [
        f"export AGENT_BENCH_ROOT={shlex.quote(str(repo))}",
        f"export PLAYWRIGHT_BROWSERS_PATH={shlex.quote(os.environ['PLAYWRIGHT_BROWSERS_PATH'])}",
        f"export HOME={shlex.quote(os.environ['HOME'])}",
    ]
    ld = os.environ.get("LD_LIBRARY_PATH", "")
    if ld:
        lines.append(f"export LD_LIBRARY_PATH={shlex.quote(ld)}")
    return lines


def apply_playwright_env_to(
    target: dict[str, str],
    root: Path | None = None,
    *,
    install_vendor_libs: bool = False,
) -> dict[str, str]:
    """Merge shared Chromium paths into a subprocess env (Ouroboros workers, CLI)."""
    ensure_chromium_runtime(root, install_vendor_libs=install_vendor_libs)
    for key in (
        "AGENT_BENCH_ROOT",
        "PLAYWRIGHT_BROWSERS_PATH",
        "HOME",
        "LD_LIBRARY_PATH",
        "PLAYWRIGHT_INSTALL_WITH_DEPS",
        "SKIP_PLAYWRIGHT_INSTALL_DEPS",
    ):
        if key in os.environ:
            target[key] = os.environ[key]
    target.setdefault("PLAYWRIGHT_INSTALL_WITH_DEPS", "0")
    target.setdefault("SKIP_PLAYWRIGHT_INSTALL_DEPS", "1")
    return target

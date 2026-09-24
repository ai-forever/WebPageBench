"""Downloads must be enabled in the eval browser profile.

The «Файлы» tasks (``files_download_*`` / ``files_archive_*``) are only
solvable if the agent's browser can actually save a file. Two things break that:

* ``chrome-headless-shell`` has no download manager, and it used to be preferred
  for every headless run;
* ``BrowserProfile`` was built without ``accept_downloads`` / ``downloads_path``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench_eval.browser_profile import (
    _discover_playwright_chromium_bins,
    downloads_dir,
    find_browser_executable,
)
from bench_eval.config import EvalConfig

BENCH_TASKS_DIR = Path(__file__).resolve().parents[2] / "tests" / "bench" / "tasks"
DOWNLOAD_EVENT = "bench_files_download"


class TestDownloadsDir:
    def test_defaults_to_output_dir(self, tmp_path: Path):
        config = EvalConfig(eval_output_dir=str(tmp_path / "run"))
        target = downloads_dir(config)
        assert target == tmp_path / "run" / "downloads"
        assert target.is_dir()

    def test_explicit_dir_wins(self, tmp_path: Path):
        explicit = tmp_path / "custom-dl"
        config = EvalConfig(
            eval_output_dir=str(tmp_path / "run"),
            agent_downloads_dir=str(explicit),
        )
        assert downloads_dir(config) == explicit
        assert explicit.is_dir()

    def test_disabled_returns_none(self, tmp_path: Path):
        config = EvalConfig(
            eval_output_dir=str(tmp_path / "run"),
            agent_downloads_enabled=False,
        )
        assert downloads_dir(config) is None


class TestBrowserExecutableChoice:
    """Downloads force full Chromium; headless-shell stays the default otherwise."""

    def _fake_playwright_root(self, tmp_path: Path) -> tuple[Path, Path]:
        full = (
            tmp_path
            / "chromium-1200"
            / "chrome-mac"
            / "Chromium.app"
            / "Contents"
            / "MacOS"
            / "Chromium"
        )
        shell = (
            tmp_path
            / "chromium_headless_shell-1200"
            / "chrome-mac"
            / "Chromium.app"
            / "Contents"
            / "MacOS"
            / "Chromium"
        )
        for path in (full, shell):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o755)
        return full, shell

    def test_discovery_finds_both_builds(self, tmp_path: Path):
        full, shell = self._fake_playwright_root(tmp_path)
        found_full, found_shell = _discover_playwright_chromium_bins(tmp_path)
        assert str(full) in found_full
        assert str(shell) in found_shell

    def test_discovery_handles_current_playwright_layout(self, tmp_path: Path):
        """Recent builds use "Google Chrome for Testing.app" and per-arch shell
        dirs (chrome-headless-shell-mac-arm64), not the legacy Chromium.app /
        chrome-headless-shell-linux64 names."""
        full = (
            tmp_path
            / "chromium-1228"
            / "chrome-mac-arm64"
            / "Google Chrome for Testing.app"
            / "Contents"
            / "MacOS"
            / "Google Chrome for Testing"
        )
        shell = (
            tmp_path
            / "chromium_headless_shell-1228"
            / "chrome-headless-shell-mac-arm64"
            / "chrome-headless-shell"
        )
        for path in (full, shell):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o755)

        found_full, found_shell = _discover_playwright_chromium_bins(tmp_path)
        assert str(full) in found_full
        assert str(shell) in found_shell

    def test_discovery_skips_helper_and_nonexecutable_entries(self, tmp_path: Path):
        base = tmp_path / "chromium-1228" / "chrome-mac-arm64"
        helper = (
            base
            / "Google Chrome for Testing.app"
            / "Contents"
            / "MacOS"
            / "Google Chrome for Testing Helper"
        )
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text("#!/bin/sh\n", encoding="utf-8")
        helper.chmod(0o755)

        not_exec = base / "Other.app" / "Contents" / "MacOS" / "Other"
        not_exec.parent.mkdir(parents=True, exist_ok=True)
        not_exec.write_text("data", encoding="utf-8")
        not_exec.chmod(0o644)

        found_full, _ = _discover_playwright_chromium_bins(tmp_path)
        assert found_full == []

    def test_headless_without_downloads_prefers_headless_shell(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        _, shell = self._fake_playwright_root(tmp_path)
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
        monkeypatch.delenv("AGENT_BROWSER_EXECUTABLE", raising=False)
        monkeypatch.delenv("BROWSER_EXECUTABLE_PATH", raising=False)
        config = EvalConfig(agent_headless=True, agent_downloads_enabled=False)
        assert find_browser_executable(config) == str(shell)

    def test_headless_with_downloads_uses_full_chromium(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        full, _ = self._fake_playwright_root(tmp_path)
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
        monkeypatch.delenv("AGENT_BROWSER_EXECUTABLE", raising=False)
        monkeypatch.delenv("BROWSER_EXECUTABLE_PATH", raising=False)
        config = EvalConfig(agent_headless=True, agent_downloads_enabled=True)
        assert find_browser_executable(config) == str(full)


@pytest.fixture(scope="module")
def download_tasks() -> dict[str, dict]:
    found = {}
    for path in sorted(BENCH_TASKS_DIR.glob("*.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        conditions = task["test_data"].get("conditions") or []
        if any(c.get("event_name") == DOWNLOAD_EVENT for c in conditions):
            found[path.stem] = task
    return found


class TestDownloadTasksAreCovered:
    """Guard the reason downloads exist at all: real tasks depend on them."""

    def test_download_tasks_exist(self, download_tasks: dict[str, dict]):
        assert download_tasks, f"no bench task emits {DOWNLOAD_EVENT}"

    def test_downloads_enabled_by_default(self):
        assert EvalConfig().agent_downloads_enabled is True

    def test_each_download_task_pins_year_and_file(
        self, download_tasks: dict[str, dict]
    ):
        for stem, task in download_tasks.items():
            conditions = task["test_data"]["conditions"]
            download = next(
                c for c in conditions if c.get("event_name") == DOWNLOAD_EVENT
            )
            params = download.get("parameters") or {}
            assert params.get("year"), stem
            assert params.get("collection"), stem
            assert params.get("format") in {"pdf", "csv"}, stem
            assert params.get("file"), stem

    def test_download_files_exist_on_disk(
        self, download_tasks: dict[str, dict]
    ):
        """A task must name a file that is served from public/mocks/files/."""
        files_dir = (
            BENCH_TASKS_DIR.parents[2]
            / "site"
            / "frontend"
            / "public"
            / "mocks"
            / "files"
        )
        config = json.loads(
            (BENCH_TASKS_DIR.parent / "config.json").read_text(encoding="utf-8")
        )
        collections = {
            item["id"]: item
            for item in config["domain_configs"]["files"]["collections"]
        }

        for stem, task in download_tasks.items():
            download = next(
                c
                for c in task["test_data"]["conditions"]
                if c.get("event_name") == DOWNLOAD_EVENT
            )
            params = download["parameters"]
            collection = collections[params["collection"]]
            year_files = collection["years"][str(params["year"])]
            names = {row["file"] for row in year_files}
            assert params["file"] in names, f"{stem}: {params['file']!r} not in {names}"
            assert (files_dir / params["file"]).is_file(), f"{stem}: missing {params['file']}"

    def test_catalog_files_all_exist_and_years_vary(self):
        files_dir = (
            BENCH_TASKS_DIR.parents[2]
            / "site"
            / "frontend"
            / "public"
            / "mocks"
            / "files"
        )
        config = json.loads(
            (BENCH_TASKS_DIR.parent / "config.json").read_text(encoding="utf-8")
        )
        collections = config["domain_configs"]["files"]["collections"]
        year_lengths: list[int] = []
        archive_lengths: dict[str, int] = {}

        for item in collections:
            for year, rows in item["years"].items():
                names = [row["file"] for row in rows]
                assert len(names) >= 2, f"{item['id']}/{year}: expected >=2 files, got {len(names)}"
                year_lengths.append(len(names))
                if item["id"] == "project_archive":
                    assert len(names) >= 10, f"archive {year}: expected >=10, got {len(names)}"
                    archive_lengths[str(year)] = len(names)
                for name in names:
                    assert (files_dir / name).is_file(), f"missing mock {name}"

        assert len(set(year_lengths)) > 1, year_lengths
        assert archive_lengths.get("2023") != archive_lengths.get("2024"), archive_lengths

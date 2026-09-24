"""Manage ouroboros drive roots across eval tasks."""

from __future__ import annotations

import json
import os
import shutil
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bench_eval.config import EvalConfig
from bench_eval.ouroboros_config import OuroborosHarnessConfig, load_ouroboros_harness_config
from bench_eval.results import resolve_output_dir

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BUNDLED_SEED_MEMORY = _REPO_ROOT / "configs" / "ouroboros" / "seed" / "memory"
_ISOLATED_SENTINEL = ".ouroboros_isolated_benchmark"
_IDENTITY_FILES = ("identity.md", "WORLD.md", "registry.md")
_MEMORY_DIRNAME = "memory"


def _sanitize_drive_namespace(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    return safe or "run"


def resolve_ouroboros_drive_namespace(config: EvalConfig) -> str:
    """
    Per-run namespace under ``ouroboros_drive/`` so concurrent eval processes
    can share ``EVAL_OUTPUT_DIR`` without clobbering shared evolving drives.
    """
    suffix = config.track_suffix or os.environ.get("EVAL_TRACK_SUFFIX")
    if suffix:
        return _sanitize_drive_namespace(suffix)
    generated = uuid.uuid4().hex[:8]
    os.environ.setdefault("EVAL_TRACK_SUFFIX", generated)
    return generated


@dataclass
class OuroborosTaskDrive:
    task_key: str
    drive_root: Path
    memory_mode: str
    mode: str


def normalize_to_memory_seed_dir(path: Path) -> Optional[Path]:
    """Return a memory/ directory that contains identity seed files."""
    candidate = path.expanduser()
    if not candidate.exists():
        return None
    if candidate.name == _MEMORY_DIRNAME and (candidate / "identity.md").is_file():
        return candidate
    if (candidate / "identity.md").is_file():
        return candidate
    memory_subdir = candidate / _MEMORY_DIRNAME
    if memory_subdir.is_dir() and (memory_subdir / "identity.md").is_file():
        return memory_subdir
    return None


def resolve_identity_seed_memory_dir(env: Optional[dict[str, str]] = None) -> Path:
    """
    Resolve the memory/ directory used to seed full ouroboros drives.

    Precedence:
    1. ``OUROBOROS_IDENTITY_SEED_DIR`` (data root or memory/ path)
    2. ``OUROBOROS_REPO_DIR`` → ``data/memory`` then ``data``
    3. ``~/Ouroboros/data/memory`` (desktop install)
    4. Bundled ``configs/ouroboros/seed/memory`` in WebPageBench
    """
    env = env if env is not None else os.environ
    candidates: list[Path] = []

    env_seed = env.get("OUROBOROS_IDENTITY_SEED_DIR")
    if env_seed:
        candidates.append(Path(env_seed))

    repo_seed = env.get("OUROBOROS_REPO_DIR")
    if repo_seed:
        repo_path = Path(repo_seed).expanduser()
        candidates.extend(
            [
                repo_path / "data" / _MEMORY_DIRNAME,
                repo_path / "data",
            ]
        )

    home_data = Path.home() / "Ouroboros" / "data"
    candidates.extend(
        [
            home_data / _MEMORY_DIRNAME,
            home_data,
        ]
    )
    candidates.append(_BUNDLED_SEED_MEMORY)

    for candidate in candidates:
        resolved = normalize_to_memory_seed_dir(candidate)
        if resolved is not None:
            return resolved

    return _BUNDLED_SEED_MEMORY


class OuroborosEvalSession:
    """Session-scoped drive manager for ouroboros harness modes."""

    def __init__(
        self,
        config: OuroborosHarnessConfig,
        *,
        eval_output_dir: Path,
        run_namespace: str,
        max_retries: int = 3,
    ) -> None:
        self._config = config
        self._eval_output_dir = eval_output_dir
        self._run_namespace = _sanitize_drive_namespace(run_namespace)
        self._max_retries = max_retries
        self._lock = threading.Lock()
        self._shared_drive: Optional[Path] = None
        self._identity_seed: Optional[Path] = None

    @classmethod
    def from_eval_config(cls, config: EvalConfig) -> Optional["OuroborosEvalSession"]:
        mode = _resolve_mode_from_agent_harness(config.agent_harness)
        if mode is None:
            return None
        ouroboros_config = load_ouroboros_harness_config(
            config.ouroboros_config_path,
            mode=mode,
        )
        return cls(
            ouroboros_config,
            eval_output_dir=resolve_output_dir(config),
            run_namespace=resolve_ouroboros_drive_namespace(config),
            max_retries=config.llm_max_retries,
        )

    def prepare_task_drive(self, task_key: str) -> OuroborosTaskDrive:
        with self._lock:
            if self._config.shared_drive:
                drive_root = self._shared_drive_path()
            else:
                drive_root = self._per_task_drive_path(task_key)
                if drive_root.exists():
                    shutil.rmtree(drive_root)
                drive_root.mkdir(parents=True, exist_ok=True)
                (drive_root / _ISOLATED_SENTINEL).write_text(
                    "isolated benchmark data root\n",
                    encoding="utf-8",
                )
            self._seed_drive(drive_root)
            return OuroborosTaskDrive(
                task_key=task_key,
                drive_root=drive_root,
                memory_mode=self._config.memory_mode,
                mode=self._config.mode,
            )

    def finalize_task(self, task_drive: OuroborosTaskDrive, *, agent_summary: dict) -> None:
        if self._config.evolution_enabled:
            self._record_evolution_marker(task_drive, agent_summary)
            self._trigger_post_task_evolution(task_drive)

    def _record_evolution_marker(self, task_drive: OuroborosTaskDrive, agent_summary: dict) -> None:
        marker = {
            "task_key": task_drive.task_key,
            "mode": task_drive.mode,
            "is_done": bool(agent_summary.get("is_done")),
            "steps": int(agent_summary.get("steps") or 0),
            "final_result": agent_summary.get("final_result"),
        }
        evolution_log = task_drive.drive_root / "state" / "dab_evolution_markers.jsonl"
        evolution_log.parent.mkdir(parents=True, exist_ok=True)
        with evolution_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(marker, ensure_ascii=False) + "\n")

    def _trigger_post_task_evolution(self, task_drive: OuroborosTaskDrive) -> None:
        if not self._config.ouroboros_url:
            return
        try:
            from bench_eval.ouroboros_client import OuroborosHTTPClient
            from bench_eval.ouroboros_llm_sync import sync_ouroboros_server_llm

            client = OuroborosHTTPClient(
                self._config.ouroboros_url,
                timeout=15.0,
                max_retries=self._max_retries,
            )
            sync_ouroboros_server_llm(client)
            client.set_post_task_evolution(True)
            client.request(
                "POST",
                "/api/command",
                {
                    "cmd": (
                        "/evolve on "
                        f"WebPageBench task {task_drive.task_key}: incorporate learnings for next web task"
                    )
                },
            )
            client.wait_until_ready(
                label=f"Ouroboros API (post-evolve, task={task_drive.task_key})",
            )
        except Exception as exc:
            print(
                f"[ouroboros] post-task evolution wait failed for "
                f"{task_drive.task_key}: {exc}",
                flush=True,
            )
            return

    def _ouroboros_drive_root(self) -> Path:
        return self._eval_output_dir / "ouroboros_drive" / self._run_namespace

    def _shared_drive_path(self) -> Path:
        if self._shared_drive is None:
            self._shared_drive = self._ouroboros_drive_root() / "shared"
            self._shared_drive.mkdir(parents=True, exist_ok=True)
            (self._shared_drive / _ISOLATED_SENTINEL).write_text(
                "isolated benchmark data root\n",
                encoding="utf-8",
            )
        return self._shared_drive

    def _per_task_drive_path(self, task_key: str) -> Path:
        safe_key = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in task_key)
        return self._ouroboros_drive_root() / "tasks" / safe_key

    def _seed_drive(self, drive_root: Path) -> None:
        if not self._config.include_identity:
            return
        seed_memory = self._identity_seed_memory_path()
        if seed_memory is None or not seed_memory.exists():
            return
        target_memory = drive_root / _MEMORY_DIRNAME
        target_memory.mkdir(parents=True, exist_ok=True)
        for name in _IDENTITY_FILES:
            source = seed_memory / name
            if source.is_file():
                target = target_memory / name
                if not target.exists():
                    shutil.copy2(source, target)
        self._copy_seed_knowledge(seed_memory, target_memory)

    def _copy_seed_knowledge(self, seed_memory: Path, target_memory: Path) -> None:
        source_knowledge = seed_memory / "knowledge"
        if not source_knowledge.is_dir():
            return
        target_knowledge = target_memory / "knowledge"
        for item in source_knowledge.rglob("*"):
            if not item.is_file():
                continue
            relative = item.relative_to(source_knowledge)
            target = target_knowledge / relative
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    def _identity_seed_memory_path(self) -> Optional[Path]:
        if self._identity_seed is not None:
            return self._identity_seed
        self._identity_seed = resolve_identity_seed_memory_dir()
        return self._identity_seed


_SESSION: Optional[OuroborosEvalSession] = None
_SESSION_LOCK = threading.Lock()


def get_ouroboros_session(config: EvalConfig) -> Optional[OuroborosEvalSession]:
    global _SESSION
    with _SESSION_LOCK:
        if _SESSION is None:
            _SESSION = OuroborosEvalSession.from_eval_config(config)
        return _SESSION


def reset_ouroboros_session() -> None:
    global _SESSION
    with _SESSION_LOCK:
        _SESSION = None


def _resolve_mode_from_agent_harness(agent_harness: str) -> Optional[str]:
    from bench_eval.harness_names import normalize_harness_name

    try:
        harness = normalize_harness_name(agent_harness)
    except ValueError:
        return None
    mapping = {
        "ouroboros-cut": "cut",
        "ouroboros-full-isolated": "full_isolated",
        "ouroboros-full-evolving": "full_evolving",
    }
    return mapping.get(harness)

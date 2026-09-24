"""Smoke and regression tests for parallel eval runs (--num-processes)."""

from __future__ import annotations

import json
import os
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

COMMON_ENV = _REPO_ROOT / "envs" / "_common.env"
EVAL_ENV_SH = _REPO_ROOT / "scripts" / "_eval_env.sh"
PARALLEL_SMOKE_SCRIPT = _REPO_ROOT / "scripts" / "run_eval_parallel_smoke.sh"
# run_eval_parallel_smoke.sh drives 5 workers to verify xdist distribution.
EXPECTED_WORKER_COUNT = 5
# envs/_common.env deliberately ships a lower default because five Chromium
# workers overload constrained local environments.
COMMON_ENV_WORKER_COUNT = 2
SMOKE_TASK_FILTER = "ecommerce_basket"
SMOKE_RUN_ENV = "ouroboros-cut/deepseek-v4-flash"


def _bash_with_assoc_arrays() -> str | None:
    """scripts/_eval_env.sh needs `declare -A` (bash >= 4); macOS ships bash 3.2."""
    for candidate in ("bash", "/opt/homebrew/bin/bash", "/usr/local/bin/bash"):
        try:
            probe = subprocess.run(
                [candidate, "-c", "declare -A _probe=() 2>/dev/null"],
                capture_output=True,
                text=True,
            )
        except OSError:
            continue
        if probe.returncode == 0:
            return candidate
    return None


BASH4 = _bash_with_assoc_arrays()

requires_bash4 = pytest.mark.skipif(
    BASH4 is None,
    reason="scripts/_eval_env.sh requires bash >= 4 (declare -A); none found on PATH",
)


def _deepeval_cmd() -> list[str] | None:
    """Resolve the deepeval CLI. The package has no __main__, so `-m deepeval`
    is not a usable fallback — return None and let the caller skip."""
    deepeval_bin = Path.home() / ".local" / "bin" / "deepeval"
    if deepeval_bin.is_file():
        return [str(deepeval_bin)]
    on_path = shutil.which("deepeval")
    if on_path:
        return [on_path]
    return None


def test_common_env_sets_conservative_num_processes():
    text = COMMON_ENV.read_text(encoding="utf-8")
    assert f'DEEPEVAL_EXTRA_ARGS="--num-processes {COMMON_ENV_WORKER_COUNT}"' in text


@requires_bash4
def test_eval_env_passes_deepeval_extra_args_num_processes():
    script = f"""
set -euo pipefail
export DEEPEVAL_EXTRA_ARGS="--num-processes 5"
source "{EVAL_ENV_SH}"
printf '%s\\n' "${{DEEPEVAL_EXTRA_ARGS}}"
"""
    completed = subprocess.run(
        [BASH4, "-c", script],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "--num-processes 5"


@requires_bash4
def test_eval_env_sets_deepeval_cache_under_output_dir():
    script = f"""
set -euo pipefail
unset DEEPEVAL_CACHE_FOLDER EVAL_OUTPUT_DIR EVAL_DATASET_PATH EVAL_TRACK_SUFFIX
export EVAL_ENV_FILE=/dev/null
export LLM_MODEL=gpt-4.1-mini
export AGENT_HARNESS=browser-use
source "{EVAL_ENV_SH}"
_eval_load_dotenv
_eval_prepare_output_dir
printf 'OUTPUT=%s\\n' "$EVAL_OUTPUT_DIR"
printf 'CACHE=%s\\n' "$DEEPEVAL_CACHE_FOLDER"
"""
    completed = subprocess.run(
        [BASH4, "-c", script],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = dict(
        line.split("=", 1) for line in completed.stdout.strip().splitlines()
    )
    assert lines["OUTPUT"]
    assert lines["CACHE"] == f"{lines['OUTPUT']}/.deepeval"
    assert "__" in lines["OUTPUT"]


@requires_bash4
def test_eval_env_preserves_deepeval_extra_args_override():
    script = f"""
set -euo pipefail
export DEEPEVAL_EXTRA_ARGS="--num-processes 1"
source "{EVAL_ENV_SH}"
_eval_resolve_env_file browser-use/gemini-2.5-flash
_eval_load_dotenv
printf '%s\\n' "${{DEEPEVAL_EXTRA_ARGS}}"
"""
    completed = subprocess.run(
        [BASH4, "-c", script],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "--num-processes 1"


def test_ouroboros_server_launch_clears_pythonpath():
    text = (_REPO_ROOT / "scripts" / "_resolve_ouroboros_bin.sh").read_text(encoding="utf-8")
    assert "_run_ouroboros_server()" in text
    assert "_verify_ouroboros_import()" in text
    assert "shell_export_lines" in text
    assert "env -u PYTHONPATH" not in text or "unset PYTHONPATH" in text
    assert "PYTHONSAFEPATH=1" in text
    assert "ouroboros_httpx_hook" in text
    assert "PLAYWRIGHT_BROWSERS_PATH" in text
    assert "LD_LIBRARY_PATH" in text


def test_parallel_smoke_script_matches_documented_command():
    """Parallel smoke needs >= worker-count tasks to verify distribution."""
    text = PARALLEL_SMOKE_SCRIPT.read_text(encoding="utf-8")
    assert 'DEEPEVAL_EXTRA_ARGS="${DEEPEVAL_EXTRA_ARGS:---num-processes 5}"' in text
    assert 'EVAL_MAX_TASKS="${EVAL_MAX_TASKS:-$EXPECTED_WORKERS}"' in text
    assert f'EVAL_TASK_FILTER="${{EVAL_TASK_FILTER:-{SMOKE_TASK_FILTER}}}"' in text
    assert 'EVAL_REBUILD_DATASET="${EVAL_REBUILD_DATASET:-true}"' in text
    assert "run_eval.sh" in text
    assert SMOKE_RUN_ENV in text
    assert "worker_count" in text


@requires_bash4
def test_parallel_smoke_max_tasks_defaults_to_worker_count():
    script = f"""
set -euo pipefail
source "{PARALLEL_SMOKE_SCRIPT}"
"""
    # Sourcing runs run_eval.sh; stop after env is set by overriding run_eval.sh.
    script = f"""
set -euo pipefail
ROOT="{_REPO_ROOT}"
RUN_ENV="{SMOKE_RUN_ENV}"
DEEPEVAL_EXTRA_ARGS="--num-processes {EXPECTED_WORKER_COUNT}"
_parallel_smoke_expected_workers() {{
  local extra="${{DEEPEVAL_EXTRA_ARGS:-}}"
  if [[ "$extra" =~ --num-processes[[:space:]]+([0-9]+) ]]; then
    echo "${{BASH_REMATCH[1]}}"
    return 0
  fi
  echo 5
}}
EXPECTED_WORKERS="$(_parallel_smoke_expected_workers)"
EVAL_MAX_TASKS="${{EVAL_MAX_TASKS:-$EXPECTED_WORKERS}}"
printf 'EVAL_MAX_TASKS=%s\\n' "$EVAL_MAX_TASKS"
"""
    completed = subprocess.run(
        [BASH4, "-c", script],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == f"EVAL_MAX_TASKS={EXPECTED_WORKER_COUNT}"


def test_parallel_smoke_validator_rejects_fewer_tasks_than_workers(tmp_path: Path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "results.json").write_text(
        json.dumps(
            {
                "run": {
                    "total_tasks": 1,
                    "parallel": {"worker_count": 1, "worker_ids": ["gw0"]},
                },
                "tests": [{"test_name": "ecommerce_basket_any_product"}],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "results.worker-gw0.json").write_text("{}", encoding="utf-8")
    validator = f"""
import json, os, re, sys
from pathlib import Path
output_dir = Path("{tmp_path}")
extra_args = "--num-processes 5"
match = re.search(r"--num-processes\\s+(\\d+)", extra_args)
expected_workers = int(match.group(1)) if match else 1
max_tasks = 1
payload = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
parallel = (payload.get("run") or {{}}).get("parallel") or {{}}
errors = []
if max_tasks < expected_workers:
    errors.append("EVAL_MAX_TASKS too low")
if parallel.get("worker_count") != expected_workers:
    errors.append("worker_count mismatch")
sys.exit(1 if errors else 0)
"""
    completed = subprocess.run(
        [sys.executable, "-c", validator],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1


@pytest.mark.integration
def test_parallel_smoke_deepeval_num_processes_five(tmp_path: Path):
    """Verify deepeval honors --num-processes 5 (infra smoke, no WebPageBench/LLM)."""
    deepeval_cmd = _deepeval_cmd()
    if deepeval_cmd is None:
        pytest.skip("deepeval CLI not installed (pip install -e ./deepeval)")
    if shutil.which("py.test") is None and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist not installed; --num-processes needs it")
    output_dir = tmp_path / "parallel-smoke"
    smoke_test = tmp_path / "test_parallel_workers.py"
    smoke_test.write_text(
        """
import os
import pytest

@pytest.mark.parametrize("task_id", range(5))
def test_worker_records_xdist_id(task_id):
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    assert worker and worker != "master"
""",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.update(
        {
            "EVAL_OUTPUT_DIR": str(output_dir),
            "EVAL_SHOW_PROGRESS": "false",
            "PYTHONPATH": f"{_REPO_ROOT / 'lib' / 'src'}:{_REPO_ROOT}",
            "PATH": f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}",
        }
    )
    completed = subprocess.run(
        [
            *deepeval_cmd,
            "test",
            "run",
            str(smoke_test),
            "--identifier",
            "parallel-smoke-pytest",
            "--num-processes",
            str(EXPECTED_WORKER_COUNT),
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "bringing up nodes" in completed.stdout.lower() + completed.stderr.lower()


@requires_bash4
def test_eval_run_deepeval_builds_extra_args_from_env():
    """Same word-splitting as _eval_run_deepeval uses for DEEPEVAL_EXTRA_ARGS."""
    script = f"""
set -euo pipefail
source "{EVAL_ENV_SH}"
export DEEPEVAL_EXTRA_ARGS="--num-processes {EXPECTED_WORKER_COUNT}"
extra=($DEEPEVAL_EXTRA_ARGS)
printf '%s\\n' "${{extra[@]}}"
"""
    completed = subprocess.run(
        [BASH4, "-c", script],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.splitlines() == [
        "--num-processes",
        str(EXPECTED_WORKER_COUNT),
    ]

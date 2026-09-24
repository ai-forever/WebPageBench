#!/usr/bin/env bash
# Parallel eval smoke: N real bench tasks via run_eval.sh + pytest-xdist workers.
#
# WebPageBench (backend + frontend) must be running: ./scripts/start_dab.sh
# LLM keys: envs/_openrouter.env or .env (see envs/runs/*)
#
#   ./scripts/run_eval_parallel_smoke.sh
#   ./scripts/run_eval_parallel_smoke.sh browser-use/gemini-2.5-flash
#
# Equivalent to:
#   EVAL_MAX_TASKS=5 \
#   EVAL_TASK_FILTER=ecommerce_basket \
#   EVAL_REBUILD_DATASET=true \
#   DEEPEVAL_EXTRA_ARGS="--num-processes 5" \
#   ./scripts/run_eval.sh ouroboros-cut/deepseek-v4-flash
#
# EVAL_MAX_TASKS defaults to the worker count from DEEPEVAL_EXTRA_ARGS so each
# xdist worker gets at least one task. Use EVAL_MAX_TASKS=1 only for a cheap
# single-task smoke — it does not exercise parallel distribution.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

_parallel_smoke_expected_workers() {
  local extra="${DEEPEVAL_EXTRA_ARGS:-}"
  if [[ "$extra" =~ --num-processes[[:space:]]+([0-9]+) ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$extra" =~ (^|[[:space:]])-n[[:space:]]+([0-9]+) ]]; then
    echo "${BASH_REMATCH[2]}"
    return 0
  fi
  echo 5
}

RUN_ENV="${1:-ouroboros-cut/deepseek-v4-flash}"
if [[ $# -gt 0 ]]; then
  shift
fi

# Before run_eval.sh sources _eval_env.sh (default there is --num-processes 2).
export DEEPEVAL_EXTRA_ARGS="${DEEPEVAL_EXTRA_ARGS:---num-processes 5}"
EXPECTED_WORKERS="$(_parallel_smoke_expected_workers)"
export EVAL_MAX_TASKS="${EVAL_MAX_TASKS:-$EXPECTED_WORKERS}"
export EVAL_TASK_FILTER="${EVAL_TASK_FILTER:-ecommerce_basket}"
export EVAL_REBUILD_DATASET="${EVAL_REBUILD_DATASET:-true}"

"$ROOT/scripts/run_eval.sh" "$RUN_ENV" "$@"

python3 - <<'PY'
import json
import os
import re
import sys
from pathlib import Path

from bench_eval.results import list_worker_result_files

output_dir = Path(os.environ["EVAL_OUTPUT_DIR"])
extra_args = os.environ.get("DEEPEVAL_EXTRA_ARGS", "")
match = re.search(r"--num-processes\s+(\d+)", extra_args)
if not match:
    match = re.search(r"(?:^|\s)-n\s+(\d+)", extra_args)
expected_workers = int(match.group(1)) if match else 1
max_tasks = int(os.environ.get("EVAL_MAX_TASKS", expected_workers))

results_path = output_dir / "results.json"
if not results_path.is_file():
    print(f"Missing results.json in {output_dir}", file=sys.stderr)
    sys.exit(1)

payload = json.loads(results_path.read_text(encoding="utf-8"))
run = payload.get("run") or {}
parallel = run.get("parallel") or {}
worker_count = parallel.get("worker_count")
worker_ids = parallel.get("worker_ids") or []
worker_files = list_worker_result_files(output_dir)
total_tasks = run.get("total_tasks")

errors = []
if max_tasks < expected_workers:
    errors.append(
        f"EVAL_MAX_TASKS={max_tasks} < {expected_workers} workers: "
        "parallel distribution cannot be verified; raise EVAL_MAX_TASKS "
        "or lower --num-processes"
    )
if total_tasks != max_tasks:
    errors.append(f"total_tasks={total_tasks!r}, expected {max_tasks}")
if worker_count != expected_workers:
    errors.append(
        f"worker_count={worker_count!r}, expected {expected_workers} "
        f"from DEEPEVAL_EXTRA_ARGS={extra_args!r}"
    )
if len(worker_files) != expected_workers:
    errors.append(
        f"found {len(worker_files)} worker files, expected {expected_workers}"
    )
if len(worker_ids) != expected_workers:
    errors.append(
        f"worker_ids={worker_ids!r}, expected {expected_workers} entries"
    )

if errors:
    for message in errors:
        print(message, file=sys.stderr)
    sys.exit(1)

print(
    f"Parallel smoke OK: {worker_count} workers "
    f"({', '.join(worker_ids)}), {total_tasks} tasks → {results_path}"
)
PY

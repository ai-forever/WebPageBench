#!/usr/bin/env bash
# Export latest eval runs into liderboard/results/ (same discovery as render_eval_aggregate.py).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/liderboard${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$REPO_ROOT/liderboard/src/export_results.py" "$@"

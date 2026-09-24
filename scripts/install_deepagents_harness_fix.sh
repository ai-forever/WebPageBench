#!/usr/bin/env bash
# Minimal deepagents harness fix without the full install_harnesses.sh flow.
#
# Usage (from repo root, inside activated .venv):
#   ./scripts/install_deepagents_harness_fix.sh
#
# Restores browser-use pins if a prior install upgraded anthropic/openai, then installs
# deepagents editable + langchain-anthropic/google-genai with --no-deps.

set -euo pipefail

ROOT="${AGENT_BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
SYNC_PINS="$ROOT/scripts/_sync_browser_use_pins.py"

echo "==> git submodule deepagents"
git submodule update --init deepagents

echo "==> Restore browser-use pins (anthropic/openai/click)"
"$PYTHON" -m pip install -e "$ROOT/browser-use"
"$PYTHON" "$SYNC_PINS" --install

echo "==> deepagents editable + runtime deps (--no-deps)"
"$PYTHON" -m pip install -e "$ROOT/deepagents/libs/deepagents" --no-deps
"$PYTHON" -m pip install --no-deps -r "$ROOT/requirements-harnesses-deepagents.txt"

if [[ -x "$ROOT/scripts/install_nodejs.sh" ]]; then
  echo "==> Node.js for Playwright MCP (skip if already installed)"
  AGENT_BENCH_ROOT="$ROOT" "$ROOT/scripts/install_nodejs.sh" || true
fi

echo "==> Verify import"
AGENT_BENCH_ROOT="$ROOT" EVAL_ROOT="$ROOT" "$PYTHON" - <<'PY'
from bench_eval.deepagents_import import import_create_deep_agent

print("OK", import_create_deep_agent())
PY

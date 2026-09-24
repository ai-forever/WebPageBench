#!/usr/bin/env bash
# Minimal openhands harness fix without full install_harnesses.sh.
#
# Usage (from repo root, inside activated .venv, Python >=3.12):
#   ./scripts/install_openhands_harness_fix.sh

set -euo pipefail

ROOT="${AGENT_BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
SYNC_PINS="$ROOT/scripts/_sync_browser_use_pins.py"

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "openhands-sdk v1.17.0 requires Python >=3.12" >&2
  "$PYTHON" -V >&2
  exit 1
fi

echo "==> git submodule openhands"
git submodule update --init openhands

echo "==> Restore browser-use (OpenHands BrowserToolSet uses it)"
"$PYTHON" -m pip install -e "$ROOT/browser-use"

echo "==> openhands-sdk + openhands-tools editable (--no-deps; keep browser-use pins)"
"$PYTHON" -m pip install -e "$ROOT/openhands/openhands-sdk" --no-deps
"$PYTHON" -m pip install -e "$ROOT/openhands/openhands-tools" --no-deps

CONSTRAINTS_FILE="$(mktemp)"
"$PYTHON" "$SYNC_PINS" --constraints >"$CONSTRAINTS_FILE" || true
if [[ -s "$CONSTRAINTS_FILE" ]]; then
  "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses-openhands.txt" -c "$CONSTRAINTS_FILE"
else
  "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses-openhands.txt"
fi
rm -f "$CONSTRAINTS_FILE"
# fastmcp 3.2.0 = OpenHands 1.17.0 lock (3.3+ drops fastmcp.mcp_config into slim)
"$PYTHON" -m pip install "fastmcp==3.2.0" --no-deps

echo "==> Re-pin browser-use after openhands extras"
"$PYTHON" -m pip install -e "$ROOT/browser-use"
"$PYTHON" "$SYNC_PINS" --install

echo "==> Verify import"
AGENT_BENCH_ROOT="$ROOT" "$PYTHON" - <<'PY'
from bench_eval.harness_compat import ensure_openhands_submodule_on_path, inspect_harness
from bench_eval.openhands_browser_patch import prepare_openhands_runtime

ensure_openhands_submodule_on_path()
prepare_openhands_runtime()
import openhands.sdk  # noqa: F401
import openhands.tools.browser_use  # noqa: F401
status = inspect_harness("openhands")
print("OK", status.ready, status.missing_packages)
if not status.ready:
    raise SystemExit(1)
PY

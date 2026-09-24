#!/usr/bin/env bash
# Playwright Chromium for local headless runs without sudo: browser in repo + conda libs.
#
# Usage (from repo root):
#   ./scripts/install_playwright_chromium.sh
#
# Optional:
#   AGENT_BENCH_ROOT=/path/to/WebPageBench
#   PLAYWRIGHT_SKIP_CONDA_LIBS=1   — only download browser, skip conda lib prefix
#   PLAYWRIGHT_INSTALL_WITH_DEPS=1 — try apt via playwright (needs sudo)

set -euo pipefail

ROOT="${AGENT_BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"

export AGENT_BENCH_ROOT="$ROOT"
export PYTHONPATH="${ROOT}/lib/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
export PLAYWRIGHT_INSTALL_WITH_DEPS="${PLAYWRIGHT_INSTALL_WITH_DEPS:-0}"

if [[ -f "${VENV_PATH:-$ROOT/.venv}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${VENV_PATH:-$ROOT/.venv}/bin/activate"
fi

ENV_FILE="$(mktemp)"
trap 'rm -f "$ENV_FILE"' EXIT

python3 - <<'PY'
from bench_eval.playwright_runtime import ensure_chromium_runtime, repo_root_from_env
import os

root = repo_root_from_env()
install_libs = os.getenv("PLAYWRIGHT_SKIP_CONDA_LIBS", "0") != "1"
ensure_chromium_runtime(root, install_vendor_libs=install_libs)
PY

python3 - <<'PY' >"$ENV_FILE"
from bench_eval.playwright_runtime import shell_export_lines, repo_root_from_env

root = repo_root_from_env()
print("\n".join(shell_export_lines(root, install_vendor_libs=False)))
PY

if ! grep -q '^export ' "$ENV_FILE"; then
  echo "Failed to write Playwright env exports; got:" >&2
  cat "$ENV_FILE" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
if [[ -n "${LD_LIBRARY_PATH:-}" ]]; then
  echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
fi

python3 -m bench_eval.playwright_preflight --install --launch-test

if [[ "${PLAYWRIGHT_INSTALL_WITH_DEPS:-0}" == "1" ]]; then
  python3 -m bench_eval.playwright_preflight --install-deps || true
  python3 -m bench_eval.playwright_preflight --launch-test
fi

echo "Playwright Chromium ready (browser + LD_LIBRARY_PATH, no sudo)."

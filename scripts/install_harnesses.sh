#!/usr/bin/env bash
# Install harness git submodules as editable packages (pinned commits).
#
# Usage (from repo root, inside activated .venv, Python >=3.12):
#   git submodule update --init deepeval browser-use hermes-ouroboros ouroboros \
#     deepagents openhands openmanus
#   pip install -r requirements-eval.txt
#   pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk
#   playwright install chromium
#   ./scripts/install_harnesses.sh
#
# openhands-sdk v1.17.0 (submodule pin) requires Python >=3.12.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
SYNC_PINS="$ROOT/scripts/_sync_browser_use_pins.py"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python не найден: $PYTHON" >&2
  exit 1
fi

cd "$ROOT"

PY_MAJOR_MINOR="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MINOR="$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')"

SUBMODULES=(
  browser-use
  deepagents
  openhands
  openmanus
)

echo "==> Python $("$PYTHON" -V) (openhands pin requires >=3.12)"

echo "==> Initializing harness submodules"
if command -v git >/dev/null 2>&1; then
  git submodule update --init "${SUBMODULES[@]}"
else
  echo "git не найден — убедитесь, что submodules уже инициализированы." >&2
fi

for path in "${SUBMODULES[@]}"; do
  if [[ ! -e "$ROOT/$path/.git" ]]; then
    echo "Submodule не инициализирован: $path" >&2
    echo "  git submodule update --init $path" >&2
    exit 1
  fi
done

echo "==> Re-pin editable browser-use before harness extras"
"$PYTHON" -m pip install -e "$ROOT/browser-use"
"$PYTHON" "$SYNC_PINS" --install

CONSTRAINTS_FILE="$(mktemp)"
trap 'rm -f "$CONSTRAINTS_FILE"' EXIT
if "$PYTHON" "$SYNC_PINS" --constraints >"$CONSTRAINTS_FILE" && [[ -s "$CONSTRAINTS_FILE" ]]; then
  echo "==> Installing harness pip deps with browser-use == pins"
  "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses.txt" -c "$CONSTRAINTS_FILE"
else
  echo "==> Installing harness pip deps (no browser-use == constraints found)"
  "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses.txt"
fi

echo "==> Installing deepagents from submodule (deepagents==0.6.11 pin, --no-deps)"
"$PYTHON" -m pip install -e "$ROOT/deepagents/libs/deepagents" --no-deps

if (( PY_MINOR >= 12 )); then
  echo "==> Installing OpenHands SDK/tools from submodule (v1.17.0 pin, --no-deps)"
  "$PYTHON" -m pip install -e "$ROOT/openhands/openhands-sdk" --no-deps
  "$PYTHON" -m pip install -e "$ROOT/openhands/openhands-tools" --no-deps
  if [[ -s "$CONSTRAINTS_FILE" ]]; then
    "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses-openhands.txt" -c "$CONSTRAINTS_FILE"
  else
    "$PYTHON" -m pip install -r "$ROOT/requirements-harnesses-openhands.txt"
  fi
  "$PYTHON" -m pip install "fastmcp==3.2.0" --no-deps
  echo "==> Verify openhands imports"
  "$PYTHON" - <<'PY'
from bench_eval.harness_compat import ensure_openhands_submodule_on_path, inspect_harness
from bench_eval.openhands_browser_patch import prepare_openhands_runtime

ensure_openhands_submodule_on_path()
prepare_openhands_runtime()
import openhands.sdk  # noqa: F401
import openhands.tools.browser_use  # noqa: F401
status = inspect_harness("openhands")
print("openhands OK", status.ready, status.missing_packages)
if not status.ready:
    raise SystemExit("openhands harness is still not ready")
PY
else
  cat >&2 <<EOF
==> SKIP openhands: submodule pin openhands-sdk v1.17.0 requires Python >=3.12
    current: Python ${PY_MAJOR_MINOR}
    deepagents / openmanus harnesses are still installed.
    For openhands use a Python 3.12+ virtual environment.
EOF
fi

echo "==> Final browser-use pin sync"
"$PYTHON" -m pip install -e "$ROOT/browser-use"
"$PYTHON" "$SYNC_PINS" --install

echo "==> deepagents runtime deps (--no-deps; keep browser-use anthropic/openai pins)"
"$PYTHON" -m pip install --no-deps -r "$ROOT/requirements-harnesses-deepagents.txt"

COMPAT_ARGS=()
if (( PY_MINOR < 12 )); then
  COMPAT_ARGS+=(--skip-harness openhands)
fi

echo "==> Harness compatibility report"
"$PYTHON" "$ROOT/scripts/check_harness_compat.py" "${COMPAT_ARGS[@]}"

# Harness pip installs can drop the ouroboros console script from the shared venv.
if [[ -e "$ROOT/ouroboros/.git" ]]; then
  local_venv="${VIRTUAL_ENV:-$ROOT/.venv}"
  if [[ ! -x "${local_venv}/bin/ouroboros" ]]; then
    echo "==> Ouroboros CLI missing after harness install; running install_ouroboros.sh"
    env -u PYTHONPATH "$ROOT/scripts/install_ouroboros.sh"
  fi
fi

echo "Done. Submodule harnesses: deepagents, openmanus, browser-use$([[ $PY_MINOR -ge 12 ]] && echo ', openhands')."

#!/usr/bin/env bash
# Поднять backend + frontend и прогнать Playwright UI-тесты раздела «Продукты».
#
#   ./scripts/run_grocery_ui_tests.sh
#   ./scripts/run_grocery_ui_tests.sh -- -k basket

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_wait_port.sh
source "$ROOT/scripts/_wait_port.sh"

API_PORT="${DAB_API_PORT:-9000}"
FRONTEND_PORT="${BENCH_FRONTEND_PORT:-5173}"

export DAB_API_PORT="$API_PORT"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:${API_PORT}/}"
export BENCH_API_ADDRESS="${BENCH_API_ADDRESS:-localhost:${API_PORT}}"
export PYTHONPATH="${ROOT}/lib/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$ROOT/site/backend" && python3 -c "import config; from main import app; app.run(host='0.0.0.0', port=config.API_PORT, debug=False, use_reloader=False)") &
BACKEND_PID=$!

(cd "$ROOT/site/frontend" && npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!

wait_port 127.0.0.1 "$API_PORT" 90 || { echo "Backend did not start on :${API_PORT}" >&2; exit 1; }
wait_port 127.0.0.1 "$FRONTEND_PORT" 120 || { echo "Frontend did not start on :${FRONTEND_PORT}" >&2; exit 1; }

cd "$ROOT"
python3 -m pytest tests/bench/test_grocery_ui.py -v --tb=short "$@"

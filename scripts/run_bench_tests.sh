#!/usr/bin/env bash
# Поднять backend + frontend, прогнать pytest бенча, остановить сервисы.
#
#   ./scripts/run_bench_tests.sh
#   ./scripts/run_bench_tests.sh -- -k hub

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
kill -0 "$BACKEND_PID" 2>/dev/null || { echo "Backend process exited" >&2; exit 1; }

wait_port 127.0.0.1 "$FRONTEND_PORT" 120 || { echo "Frontend did not start on :${FRONTEND_PORT}" >&2; exit 1; }
kill -0 "$FRONTEND_PID" 2>/dev/null || {
  echo "Frontend failed (port :${FRONTEND_PORT} busy?). Stop other Vite instances." >&2
  exit 1
}

cd "$ROOT"
python3 -m pytest tests/bench/test_verify_bench.py tests/bench/test_ui_taxonomy_tasks.py tests/bench/test_static_contract.py tests/bench/test_catalog_debrand.py tests/bench/test_condition_check.py tests/bench/test_grocery_ui.py tests/bench/test_ui_hotels.py tests/bench/test_ui_files.py tests/bench/test_ui_taxonomy.py tests/bench/test_rail_ui.py tests/bench/test_ui_variants.py tests/bench/test_domain_audit.py tests/bench/test_task_golden_paths.py -v --tb=short "$@"

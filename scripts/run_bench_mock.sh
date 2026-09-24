#!/usr/bin/env bash
# Обезличенный бенч: backend + frontend + демо-трек (без sudo).
#
#   ./scripts/run_bench_mock.sh
#   TASK=ecommerce_basket_any_product ./scripts/run_bench_mock.sh  # TRACK_ID defaults to TASK
#   TRACK_ID=my_track TASK=ecommerce_basket_any_product ./scripts/run_bench_mock.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_wait_port.sh
source "$ROOT/scripts/_wait_port.sh"

API_PORT="${DAB_API_PORT:-9000}"
FRONTEND_PORT="${BENCH_FRONTEND_PORT:-5173}"
TASK="${TASK:-ecommerce_basket_any_product}"
TRACK_ID="${TRACK_ID:-$TASK}"

export DAB_API_PORT="$API_PORT"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:${API_PORT}/}"
export BENCH_API_ADDRESS="${BENCH_API_ADDRESS:-localhost:${API_PORT}}"
export PYTHONPATH="${ROOT}/lib/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

TASK_FILE="$ROOT/tests/bench/tasks/${TASK}.json"
[[ -f "$TASK_FILE" ]] || { echo "Task not found: $TASK_FILE" >&2; exit 1; }

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

TRACK_ID="$TRACK_ID" TASK_STEM="$TASK" TASK_FILE="$TASK_FILE" API_ADDRESS="$BENCH_API_ADDRESS" ROOT="$ROOT" \
  python3 "$ROOT/scripts/_bench_create_track.py"

echo ""
echo "Хаб: http://127.0.0.1:${FRONTEND_PORT}/${TRACK_ID}/state_hub/bench_hub"
echo "API:  http://127.0.0.1:${API_PORT}/"
echo "Ctrl+C — остановить."

wait "$BACKEND_PID" "$FRONTEND_PID"

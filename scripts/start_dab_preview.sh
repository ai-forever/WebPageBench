#!/usr/bin/env bash
# Backend + production frontend (vite preview) — надёжнее для headless browser-use / eval.
#
#   ./scripts/start_dab_preview.sh
#
# Остановка: Ctrl+C

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_wait_port.sh
source "$ROOT/scripts/_wait_port.sh"

API_PORT="${DAB_API_PORT:-9000}"
FRONTEND_PORT="${BENCH_FRONTEND_PORT:-5173}"

export DAB_API_PORT="$API_PORT"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:${API_PORT}/}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Building frontend with VITE_API_URL=${VITE_API_URL} ..."
(cd "$ROOT/site/frontend" && npm run build)

(cd "$ROOT/site/backend" && python3 -c "import config; from main import app; app.run(host='0.0.0.0', port=config.API_PORT, debug=False, use_reloader=False)") &
BACKEND_PID=$!

(cd "$ROOT/site/frontend" && npm run preview -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!

wait_port 127.0.0.1 "$API_PORT" 90 || { echo "Backend did not start on :${API_PORT}" >&2; exit 1; }
kill -0 "$BACKEND_PID" 2>/dev/null || { echo "Backend process exited" >&2; exit 1; }

wait_port 127.0.0.1 "$FRONTEND_PORT" 120 || { echo "Frontend preview did not start on :${FRONTEND_PORT}" >&2; exit 1; }
kill -0 "$FRONTEND_PID" 2>/dev/null || {
  echo "Frontend preview failed (port :${FRONTEND_PORT} busy?)." >&2
  exit 1
}

echo "Backend:  http://127.0.0.1:${API_PORT}/"
echo "Frontend (preview): http://127.0.0.1:${FRONTEND_PORT}/"
echo "Ctrl+C — остановить."

wait "$BACKEND_PID" "$FRONTEND_PID"
